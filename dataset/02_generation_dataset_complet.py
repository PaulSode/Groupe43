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
NB_ADMIN_PAR_TYPE = 10
PROBA_INCOHERENCE = 0.3  # 30% de probabilité d'altérer les données d'un client
# ---------------------------------

def charger_entites_reference(chemin="entites_reference.json"):
    if not os.path.exists(chemin):
        raise RuntimeError(f"Erreur : {chemin} introuvable. Exécutez le script 01.")
    with open(chemin, "r", encoding="utf-8") as f:
        return json.load(f)

def generer_pool_b2c(taille=15):
    """Crée une base statique de clients B2C pour permettre le rapprochement documentaire."""
    return [{
        "nom": fake.last_name(), 
        "prenom": fake.first_name(), 
        "adresse": fake.address().replace('\n', ', ')
    } for _ in range(taille)]

def corrompre_chaine(texte):
    if not texte or len(texte) < 5:
        return texte
        
    vecteur = random.choice(["omission", "typo", "troncature"])
    
    if vecteur == "omission":
        mots = texte.split()
        if len(mots) > 1:
            mots.pop(random.randint(0, len(mots) - 1))
            return " ".join(mots)
    elif vecteur == "typo":
        idx = random.randint(1, len(texte) - 2)
        char_aleatoire = random.choice(string.ascii_lowercase)
        return texte[:idx] + char_aleatoire + texte[idx+1:]
    elif vecteur == "troncature":
        coupure = int(len(texte) * random.uniform(0.6, 0.9))
        return texte[:coupure]
        
    return texte

def extraire_emetteur(pool, valide=True, introduire_incoherence=False):
    """Extraction standard pour l'entité émettrice ou les documents administratifs."""
    entite = random.choice(pool).copy()
    if not valide:
        len_err = random.choice([9, 10, 12, 15])
        entite["siret"] = "".join([str(random.randint(0, 9)) for _ in range(len_err)])
    if introduire_incoherence:
        cible = random.choice(["nom", "adresse"])
        entite[cible] = corrompre_chaine(entite[cible])
    return entite

def extraire_client_b2b(pool, introduire_incoherence=False):
    """Extraction B2B garantissant au moins un champ valide pour la réconciliation."""
    entite = random.choice(pool).copy()
    if introduire_incoherence:
        champs_possibles = ["siret", "nom", "adresse"]
        # Altération de 1 ou 2 champs, laissant au moins 1 champ parfait.
        champs_a_alterer = random.sample(champs_possibles, random.choice([1, 2]))
        
        for champ in champs_a_alterer:
            if champ == "siret":
                len_err = random.choice([9, 10, 12, 15])
                entite["siret"] = "".join([str(random.randint(0, 9)) for _ in range(len_err)])
            else:
                entite[champ] = corrompre_chaine(entite[champ])
    return entite

def extraire_client_b2c(pool_b2c, introduire_incoherence=False):
    """Extraction B2C verrouillant le couple Nom/Prénom."""
    client = random.choice(pool_b2c).copy()
    if introduire_incoherence:
        client["adresse"] = corrompre_chaine(client["adresse"])
    return client

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

def creer_facture(idx, pool_b2b, pool_b2c):
    valide = random.random() > 0.2
    est_b2b = random.random() > 0.5
    
    emetteur = extraire_emetteur(pool_b2b, valide=valide)
    trans, total_ht = generer_transactions()
    tva = round(total_ht * 0.20, 2)
    
    incoherence_client = random.random() < PROBA_INCOHERENCE
    
    if est_b2b:
        entite_client = extraire_client_b2b(pool_b2b, introduire_incoherence=incoherence_client)
        # Blocage de l'auto-facturation (basé sur le nom pour éviter les faux positifs sur SIRET corrompu)
        while entite_client["nom"] == emetteur["nom"]:
             entite_client = extraire_client_b2b(pool_b2b, introduire_incoherence=incoherence_client)
             
        client_data = {
            "type": "B2B",
            "nom": entite_client["nom"],
            "siret": entite_client["siret"],
            "adresse": entite_client["adresse"]
        }
    else:
        entite_client = extraire_client_b2c(pool_b2c, introduire_incoherence=incoherence_client)
        client_data = {
            "type": "B2C",
            "nom": entite_client["nom"],
            "prenom": entite_client["prenom"],
            "adresse": entite_client["adresse"]
        }

    return {
        "type_document": "FACTURE",
        "label_classification": "facture_valide" if valide else "facture_anomalie",
        "metadonnees": {
            "numero": f"F-2026-{idx:05d}",
            "date_emission": fake.date_between(start_date='-1y', end_date='today').isoformat()
        },
        "emetteur": emetteur,
        "client": client_data,
        "transactions": trans,
        "finances": {"total_ht": total_ht, "montant_tva": tva, "total_ttc": round(total_ht + tva, 2)}
    }

def creer_devis(idx, pool_b2b, pool_b2c):
    valide = random.random() > 0.2
    signe = random.random() > 0.5
    est_b2b = random.random() > 0.5
    
    emetteur = extraire_emetteur(pool_b2b, valide=valide)
    trans, total_ht = generer_transactions(max_lignes=8)
    date_e = fake.date_between(start_date='-1y', end_date='today')
    
    incoherence_client = random.random() < PROBA_INCOHERENCE

    if est_b2b:
        entite_client = extraire_client_b2b(pool_b2b, introduire_incoherence=incoherence_client)
        while entite_client["nom"] == emetteur["nom"]:
             entite_client = extraire_client_b2b(pool_b2b, introduire_incoherence=incoherence_client)
             
        client_data = {
            "type": "B2B",
            "nom": entite_client["nom"],
            "siret": entite_client["siret"],
            "adresse": entite_client["adresse"]
        }
        nom_signataire = "La Direction"
    else:
        entite_client = extraire_client_b2c(pool_b2c, introduire_incoherence=incoherence_client)
        client_data = {
            "type": "B2C",
            "nom": entite_client["nom"],
            "prenom": entite_client["prenom"],
            "adresse": entite_client["adresse"]
        }
        nom_signataire = entite_client["prenom"]

    return {
        "type_document": "DEVIS",
        "label_classification": "devis_valide" if valide else "devis_anomalie",
        "metadonnees": {
            "numero": f"D-2026-{idx:05d}",
            "date_emission": date_e.isoformat(),
            "validite_jours": random.choice([15, 30, 60])
        },
        "emetteur": emetteur,
        "client": client_data,
        "transactions": trans,
        "finances": {"total_ht": total_ht, "total_ttc": round(total_ht * 1.2, 2)},
        "validation": {
            "est_signe": signe,
            "date_signature": (date_e + timedelta(days=2)).isoformat() if signe else None,
            "nom_signataire": nom_signataire
        }
    }

def creer_admin(type_doc, pool_b2b):
    incoherence_emetteur = random.random() < PROBA_INCOHERENCE
    entite = extraire_emetteur(pool_b2b, valide=True, introduire_incoherence=incoherence_emetteur)
    
    base = {
        "type_document": type_doc,
        "label_classification": type_doc.lower(),
        "emetteur": entite,
        "date_edition": datetime.now().strftime("%d/%m/%Y"),
        "metadonnees": {}
    }
    
    if type_doc == "SIRET":
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

def generer_tout():
    pool_b2b = charger_entites_reference()
    pool_b2c = generer_pool_b2c()
    dataset_global = []

    for i in range(1, NB_FACTURES + 1):
        dataset_global.append(creer_facture(i, pool_b2b, pool_b2c))

    for i in range(1, NB_DEVIS + 1):
        dataset_global.append(creer_devis(i, pool_b2b, pool_b2c))

    for t_admin in ["SIRET", "URSSAF", "KBIS", "RIB"]:
        for _ in range(NB_ADMIN_PAR_TYPE):
            dataset_global.append(creer_admin(t_admin, pool_b2b))

    with open("dataset_global.json", "w", encoding="utf-8") as f:
        json.dump(dataset_global, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generer_tout()