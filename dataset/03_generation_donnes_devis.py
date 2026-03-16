import random
import json
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('fr_FR')

def charger_entites_reference(chemin_fichier="entites_reference.json"):
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Fichier de référence {chemin_fichier} introuvable. Exécuter le script 01 au préalable.")

def extraire_entite(pool_entites, valide=True):
    entite = random.choice(pool_entites).copy() 
    if not valide:
        longueur_erronee = random.choice([9, 10, 12, 15])
        entite["siret"] = "".join([str(random.randint(0, 9)) for _ in range(longueur_erronee)])
    return entite

def generer_lignes_transaction():
    lignes = []
    total_ht = 0.0
    nombre_lignes = random.randint(1, 8)
    
    for _ in range(nombre_lignes):
        quantite = random.randint(1, 100)
        prix_unitaire = round(random.uniform(10.0, 2500.0), 2)
        sous_total = quantite * prix_unitaire
        total_ht += sous_total
        
        lignes.append({
            "designation": fake.catch_phrase(),
            "quantite": quantite,
            "prix_unitaire_ht": prix_unitaire,
            "sous_total_ht": round(sous_total, 2)
        })
        
    return lignes, round(total_ht, 2)

def generer_donnees_devis(numero_sequentiel, pool_entites):
    est_valide = random.random() > 0.2
    est_b2b = random.random() > 0.5
    est_signe = random.random() > 0.4 # Distribution stochastique : 60% signés, 40% non signés
    
    entite_emetteur = extraire_entite(pool_entites, valide=est_valide)
    
    transactions, total_ht = generer_lignes_transaction()
    montant_tva = round(total_ht * 0.20, 2)
    total_ttc = round(total_ht + montant_tva, 2)

    date_emission = fake.date_between(start_date='-1y', end_date='today')
    duree_validite_jours = random.choice([15, 30, 60, 90])
    date_debut_estimee = date_emission + timedelta(days=random.randint(10, 45))
    
    # Génération conditionnelle de la date de signature dans la fenêtre de validité
    date_signature = None
    if est_signe:
        date_signature = (date_emission + timedelta(days=random.randint(1, duree_validite_jours))).isoformat()

    donnees = {
        "metadonnees": {
            "type_document": "DEVIS",
            "numero_devis": f"D-{datetime.now().year}-{numero_sequentiel:05d}",
            "date_emission": date_emission.isoformat(),
            "duree_validite_jours": duree_validite_jours
        },
        "emetteur": {
            "raison_sociale": entite_emetteur["nom"],
            "adresse": entite_emetteur["adresse"],
            "siret": entite_emetteur["siret"]
        },
        "client": {
            "nom": random.choice(["Dupont", "Dupond"]),
            "prenom": random.choice(["Pierre", "Paul", "Michel", "Olivier"]),
            "adresse": fake.address().replace('\n', ', '),
            "siret_societe": extraire_entite(pool_entites, valide=True)["siret"] if est_b2b else None
        },
        "execution": {
            "date_debut_estimee": date_debut_estimee.isoformat(),
            "duree_estimee_jours": random.randint(1, 120)
        },
        "transactions": transactions,
        "finances": {
            "total_ht": total_ht,
            "taux_tva": 0.20,
            "montant_tva": montant_tva,
            "total_ttc": total_ttc
        },
        "validation": {
            "mention_requise": "Bon pour accord",
            "est_signe": est_signe,
            "date_signature": date_signature
        },
        "label_classification": "valide" if est_valide else "anomalie_siret"
    }
    
    return donnees

pool_entites_memoire = charger_entites_reference()

dataset_json = [generer_donnees_devis(i, pool_entites_memoire) for i in range(1, 6)]

chemin_sortie = "dataset_devis.json"

with open(chemin_sortie, "w", encoding="utf-8") as f:
    json.dump(dataset_json, f, indent=4, ensure_ascii=False)

print(f"Fichier généré avec succès : {chemin_sortie}")