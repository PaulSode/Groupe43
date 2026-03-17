import random
import json
import string
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('fr_FR')

# --- CONFIGURATION DES VOLUMES ---
NB_FACTURES = 20
NB_DEVIS = 20
NB_ADMIN_PAR_TYPE = 10  # (10 SIRET, 10 URSSAF, 10 KBIS, 10 RIB = 40)
# ---------------------------------

def charger_entites_reference(chemin="entites_reference.json"):
    if not os.path.exists(chemin):
        raise RuntimeError(f"Erreur : {chemin} introuvable. Exécutez le script 01.")
    with open(chemin, "r", encoding="utf-8") as f:
        return json.load(f)

def extraire_entite(pool, valide=True):
    entite = random.choice(pool).copy()
    if not valide:
        len_err = random.choice([9, 10, 12, 15])
        entite["siret"] = "".join([str(random.randint(0, 9)) for _ in range(len_err)])
    return entite

def generer_transactions(max_lignes=5):
    lignes = []
    total_ht = 0.0
    for _ in range(random.randint(1, max_lignes)):
        qte = random.randint(1, 50)
        pu = round(random.uniform(5.0, 500.0), 2)
        sous_total = round(qte * pu, 2)
        total_ht += sous_total
        lignes.append({
            "designation": fake.catch_phrase(),
            "quantite": qte,
            "prix_unitaire_ht": pu,
            "sous_total_ht": sous_total
        })
    return lignes, round(total_ht, 2)

# --- GÉNÉRATEURS SPÉCIFIQUES ---

def creer_facture(idx, pool):
    valide = random.random() > 0.2
    est_b2b = random.random() > 0.5 # 50% de chances d'être B2B
    
    emetteur = extraire_entite(pool, valide=valide)
    trans, total_ht = generer_transactions()
    tva = round(total_ht * 0.20, 2)
    
    # Génération conditionnelle du client
    if est_b2b:
        entite_client = extraire_entite(pool, valide=True)
        # On s'assure que le client n'est pas le même que l'émetteur (dans l'idéal)
        while entite_client["siret"] == emetteur["siret"]:
             entite_client = extraire_entite(pool, valide=True)
             
        client_data = {
            "type": "B2B",
            "nom": entite_client["nom"],
            "siret": entite_client["siret"],
            "adresse": entite_client["adresse"]
        }
    else:
        client_data = {
            "type": "B2C",
            "nom": fake.last_name(),
            "prenom": fake.first_name(),
            "adresse": fake.address().replace('\n', ', ')
        }

    return {
        "type_document": "FACTURE",
        "label_classification": "facture_valide" if valide else "facture_anomalie",
        "metadonnees": {
            "numero": f"F-2026-{idx:05d}",
            "date_emission": fake.date_between(start_date='-1y', end_date='today').isoformat()
        },
        "emetteur": emetteur,
        "client": client_data, # Utilisation de la nouvelle structure
        "transactions": trans,
        "finances": {"total_ht": total_ht, "montant_tva": tva, "total_ttc": round(total_ht + tva, 2)}
    }

# Dans la fonction creer_devis
def creer_devis(idx, pool):
    valide = random.random() > 0.2
    signe = random.random() > 0.5
    est_b2b = random.random() > 0.5
    
    emetteur = extraire_entite(pool, valide=valide)
    trans, total_ht = generer_transactions(max_lignes=8)
    date_e = fake.date_between(start_date='-1y', end_date='today')
    
    # Génération conditionnelle du client
    if est_b2b:
        entite_client = extraire_entite(pool, valide=True)
        while entite_client["siret"] == emetteur["siret"]:
             entite_client = extraire_entite(pool, valide=True)
             
        client_data = {
            "type": "B2B",
            "nom": entite_client["nom"],
            "siret": entite_client["siret"],
            "adresse": entite_client["adresse"]
        }
        nom_signataire = "La Direction" # Pour la signature
    else:
        prenom_fct = fake.first_name()
        client_data = {
            "type": "B2C",
            "nom": fake.last_name(),
            "prenom": prenom_fct,
            "adresse": fake.address().replace('\n', ', ')
        }
        nom_signataire = prenom_fct # Pour la signature

    return {
        "type_document": "DEVIS",
        "label_classification": "devis_valide" if valide else "devis_anomalie",
        "metadonnees": {
            "numero": f"D-2026-{idx:05d}",
            "date_emission": date_e.isoformat(),
            "validite_jours": random.choice([15, 30, 60])
        },
        "emetteur": emetteur,
        "client": client_data, # Utilisation de la nouvelle structure
        "transactions": trans,
        "finances": {"total_ht": total_ht, "total_ttc": round(total_ht * 1.2, 2)},
        "validation": {
            "est_signe": signe,
            "date_signature": (date_e + timedelta(days=2)).isoformat() if signe else None,
            "nom_signataire": nom_signataire # Ajout pour le rendu
        }
    }

def creer_admin(type_doc, pool):
    entite = extraire_entite(pool)
    base = {
        "type_document": type_doc,
        "label_classification": type_doc.lower(),
        "emetteur": entite,
        "date_edition": datetime.now().strftime("%d/%m/%Y"),
        "metadonnees": {}
    }
    
    if type_doc == "SIRET":
        # Récupération des données réelles extraites par le script 01
        base["metadonnees"] = {
            "ape": entite.get("code_ape", "99.99Z"),
            "activite": entite.get("activite_principale", "Non spécifiée"),
            "immatriculation": entite.get("date_immatriculation", "2020-01-01")
        }
    elif type_doc == "URSSAF":
        base["metadonnees"] = {
            "code_securite": "".join(random.choices(string.ascii_uppercase + string.digits, k=16)),
            "compte_urssaf": f"{random.randint(100, 999)} {random.randint(1000000, 9999999)}",
            "fin_validite": (datetime.now() + timedelta(days=180)).strftime("%d/%m/%Y")
        }
    elif type_doc == "KBIS":
        base["metadonnees"] = {
            "greffe": f"TC {fake.city().upper()}",
            "numero_gestion": f"{datetime.now().year} B {random.randint(10000, 99999)}",
            "forme_juridique": random.choice(["SAS", "SARL", "EURL"]),
            "capital": f"{random.choice([1000, 5000, 10000])} EUR"
        }
    elif type_doc == "RIB":
        iban = fake.iban()
        base["metadonnees"] = {
            "banque": fake.company(),
            "code_banque": str(random.randint(10000, 30000)),
            "code_guichet": str(random.randint(10000, 99999)),
            "numero_compte": "".join(random.choices(string.digits + string.ascii_uppercase, k=11)),
            "cle_rib": str(random.randint(10, 97)),
            "iban": " ".join([iban[i:i+4] for i in range(0, len(iban), 4)]),
            "bic": fake.swift(),
            "domiciliation": fake.address().replace('\n', ', ')
        }
    return base

# --- EXÉCUTION PRINCIPALE ---

def generer_tout():
    pool = charger_entites_reference()
    dataset_global = []

    print(f"Génération de {NB_FACTURES} factures...")
    for i in range(1, NB_FACTURES + 1):
        dataset_global.append(creer_facture(i, pool))

    print(f"Génération de {NB_DEVIS} devis...")
    for i in range(1, NB_DEVIS + 1):
        dataset_global.append(creer_devis(i, pool))

    for t_admin in ["SIRET", "URSSAF", "KBIS", "RIB"]:
        print(f"Génération de {NB_ADMIN_PAR_TYPE} documents {t_admin}...")
        for _ in range(NB_ADMIN_PAR_TYPE):
            dataset_global.append(creer_admin(t_admin, pool))

    with open("dataset_global.json", "w", encoding="utf-8") as f:
        json.dump(dataset_global, f, indent=4, ensure_ascii=False)
    
    print("-" * 30)
    print(f"SUCCÈS : {len(dataset_global)} documents compilés dans dataset_global.json")

if __name__ == "__main__":
    generer_tout()