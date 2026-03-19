import json
import os
import shutil
import subprocess
import uuid
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient
from dotenv import load_dotenv


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TESTS_DIR = os.path.dirname(__file__)
DATASET_DIR = os.path.join(ROOT_DIR, "dataset")

load_dotenv(os.path.join(ROOT_DIR, ".env"))


def _pg_config() -> dict:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "hackathon"),
        "user": os.getenv("POSTGRES_USER", "admin"),
        "password": os.getenv("POSTGRES_PASS", "admin123"),
    }


def _mongo_uri() -> str:
    user = os.getenv("MONGO_USER", "admin")
    password = os.getenv("MONGO_PASS", "admin123")
    host = os.getenv("MONGO_HOST", "localhost")
    port = os.getenv("MONGO_PORT", "27017")
    return f"mongodb://{user}:{password}@{host}:{port}/"


def _ensure_entites_reference() -> None:
    src = os.path.join(DATASET_DIR, "entites_reference.json")
    dst = os.path.join(TESTS_DIR, "entites_reference.json")
    if not os.path.exists(src):
        raise RuntimeError(f"Fichier source introuvable: {src}")
    if not os.path.exists(dst):
        shutil.copyfile(src, dst)
        print("Copie de entites_reference.json vers tests/")


def _run_generation_scripts() -> None:
    scripts = [
        "02_generation_donnees_factures.py",
        "03_generation_donnes_devis.py",
        "06_generation_donnees_admin.py",
    ]
    for script in scripts:
        print(f"Generation: {script}")
        subprocess.run(
            ["python", script],
            cwd=TESTS_DIR,
            check=True,
        )


def _load_json(path: str) -> list[dict]:
    if not os.path.exists(path):
        raise RuntimeError(f"Dataset introuvable: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _norm_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _doc_type_from_source(source_type: str) -> str:
    source_type = _norm_str(source_type).upper()
    mapping = {
        "FACTURE": "facture",
        "DEVIS": "devis",
        "SIRET": "attestation_siret",
        "URSSAF": "attestation_vigilance",
        "KBIS": "kbis",
        "RIB": "rib",
    }
    return mapping.get(source_type, "inconnu")


def _build_extracted_data(doc: dict) -> dict:
    # Datasets factures/devis
    if "metadonnees" in doc and "emetteur" in doc and "finances" in doc:
        emetteur = doc.get("emetteur", {})
        metadonnees = doc.get("metadonnees", {})
        finances = doc.get("finances", {})
        siret = _norm_str(emetteur.get("siret"))
        data = {
            "siret": siret,
            "siren": siret[:9] if len(siret) >= 9 else "",
            "tva_intracom": "",
            "raison_sociale": _norm_str(emetteur.get("raison_sociale") or emetteur.get("nom")),
            "montant_ht": str(finances.get("total_ht", "")),
            "montant_ttc": str(finances.get("total_ttc", "")),
            "taux_tva": str(float(finances.get("taux_tva", 0)) * 100).rstrip("0").rstrip("."),
            "date_emission": _norm_str(metadonnees.get("date_emission")),
            "date_expiration": "",
            "numero_document": _norm_str(
                metadonnees.get("numero_facture") or metadonnees.get("numero_devis")
            ),
            "iban": "",
            "bic": "",
        }
        return data

    # Dataset admin
    source_type = _norm_str(doc.get("type_document")).upper()
    emetteur = doc.get("emetteur", {})
    meta = doc.get("metadonnees", {})
    siret = _norm_str(emetteur.get("siret"))
    base = {
        "siret": siret,
        "siren": siret[:9] if len(siret) >= 9 else "",
        "tva_intracom": "",
        "raison_sociale": _norm_str(emetteur.get("raison_sociale") or emetteur.get("nom")),
        "montant_ht": "",
        "montant_ttc": "",
        "taux_tva": "",
        "date_emission": _norm_str(doc.get("date_edition")),
        "date_expiration": "",
        "numero_document": "",
        "iban": "",
        "bic": "",
    }

    if source_type == "URSSAF":
        base["date_expiration"] = _norm_str(meta.get("fin_validite"))
    elif source_type == "RIB":
        base["iban"] = _norm_str(meta.get("iban"))
        base["bic"] = _norm_str(meta.get("bic"))

    return base


def _expected_fields_for_type(doc_type: str) -> list[str]:
    schemas = {
        "facture": ["siret", "siren", "tva_intracom", "montant_ht", "montant_ttc", "taux_tva", "date_emission", "numero_document"],
        "devis": ["siret", "siren", "montant_ht", "montant_ttc", "taux_tva", "date_emission", "numero_document"],
        "attestation_vigilance": ["siret", "date_emission", "date_expiration"],
        "attestation_siret": ["siret", "siren", "raison_sociale"],
        "kbis": ["siret", "siren", "raison_sociale"],
        "rib": ["iban", "bic", "raison_sociale"],
    }
    return schemas.get(doc_type, [])


def _status_for_doc(doc_type: str, extracted_data: dict) -> str:
    required = _expected_fields_for_type(doc_type)
    if any(not _norm_str(extracted_data.get(f)) for f in required):
        return "manual_review"
    return "processed"


def _collect_documents() -> list[dict]:
    factures = _load_json(os.path.join(TESTS_DIR, "dataset_factures.json"))
    devis = _load_json(os.path.join(TESTS_DIR, "dataset_devis.json"))
    admin = _load_json(os.path.join(TESTS_DIR, "dataset_admin.json"))
    return factures + devis + admin


def _build_clients(docs: list[dict]) -> list[dict]:
    by_siret: dict[str, dict] = {}
    for doc in docs:
        emetteur = doc.get("emetteur", {})
        siret = _norm_str(emetteur.get("siret"))
        if not siret:
            continue
        name = _norm_str(emetteur.get("raison_sociale") or emetteur.get("nom") or "Entreprise")
        adresse = _norm_str(emetteur.get("adresse"))
        if siret not in by_siret:
            by_siret[siret] = {
                "nom": name,
                "prenom": "",
                "email": "",
                "telephone": "",
                "adresse_facturation": adresse,
                "siret": siret,
                "siren": siret[:9] if len(siret) >= 9 else "",
                "tva_intracom": "",
                "statut": "actif",
            }
    return list(by_siret.values())


def seed_postgres(documents: list[dict]) -> int:
    conn = psycopg2.connect(**_pg_config(), cursor_factory=RealDictCursor)
    inserted_docs = 0
    try:
        with conn.cursor() as cur:
            # Nettoyage des tables applicatives
            cur.execute("DELETE FROM incoherence")
            cur.execute("DELETE FROM ligne_transaction")
            cur.execute("DELETE FROM document")
            cur.execute("DELETE FROM client")

            clients = _build_clients(documents)
            client_id_by_siret: dict[str, int] = {}

            for c in clients:
                cur.execute(
                    """
                    INSERT INTO client
                    (nom, prenom, email, telephone, adresse_facturation, siret, siren, tva_intracom, statut)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id_client
                    """,
                    (
                        c["nom"], c["prenom"], c["email"], c["telephone"], c["adresse_facturation"],
                        c["siret"], c["siren"], c["tva_intracom"], c["statut"],
                    ),
                )
                client_id_by_siret[c["siret"]] = cur.fetchone()["id_client"]

            for idx, source_doc in enumerate(documents, start=1):
                if "metadonnees" in source_doc:
                    source_type = source_doc["metadonnees"].get("type_document", "")
                    date_emission = _norm_str(source_doc["metadonnees"].get("date_emission"))
                    numero = _norm_str(
                        source_doc["metadonnees"].get("numero_facture")
                        or source_doc["metadonnees"].get("numero_devis")
                    )
                else:
                    source_type = source_doc.get("type_document", "")
                    date_emission = _norm_str(source_doc.get("date_edition"))
                    numero = f"ADMIN-{idx:05d}"

                doc_type = _doc_type_from_source(source_type)
                extracted_data = _build_extracted_data(source_doc)
                status = _status_for_doc(doc_type, extracted_data)

                emetteur = source_doc.get("emetteur", {})
                siret = _norm_str(emetteur.get("siret"))
                client_id = client_id_by_siret.get(siret)
                if not client_id:
                    continue

                date_exp = _norm_str(extracted_data.get("date_expiration"))
                file_id = str(uuid.uuid4())
                filename = f"{doc_type}_{numero or idx}.pdf".replace("/", "-")
                raw_text = json.dumps(source_doc, ensure_ascii=False)

                cur.execute(
                    """
                    INSERT INTO document
                    (type_document, id_client, filename, file_path, ocr_file_id, date_emission, date_expiration,
                     statut, ocr_confidence, raw_text, extracted_data)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        doc_type,
                        client_id,
                        filename,
                        "",
                        file_id,
                        date_emission or None,
                        date_exp or None,
                        status,
                        95.0,
                        raw_text,
                        json.dumps(extracted_data, ensure_ascii=False),
                    ),
                )
                inserted_docs += 1

        conn.commit()
        return inserted_docs
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def seed_mongo(documents: list[dict]) -> int:
    db_name = os.getenv("MONGO_DB", "Data_Mongodb")
    client = MongoClient(_mongo_uri())
    db = client[db_name]
    collection = db["seed_test_documents"]
    collection.delete_many({})

    payload = []
    for idx, doc in enumerate(documents, start=1):
        payload.append(
            {
                "seed_id": idx,
                "source": "tests",
                "created_at": datetime.utcnow(),
                "raw": doc,
            }
        )
    if not payload:
        return 0
    result = collection.insert_many(payload)
    return len(result.inserted_ids)


def main() -> None:
    print("=== Seed BDD a partir des scripts tests ===")
    _ensure_entites_reference()
    _run_generation_scripts()

    docs = _collect_documents()
    print(f"Documents generes: {len(docs)}")

    nb_pg = seed_postgres(docs)
    print(f"PostgreSQL: {nb_pg} documents inseres")

    nb_mongo = seed_mongo(docs)
    print(f"MongoDB: {nb_mongo} documents seed inseres")

    print("Termine.")


if __name__ == "__main__":
    main()
