import random
import json
import string
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('fr_FR')

def charger_entites_reference(chemin="entites_reference.json"):
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError("Fichier entites_reference.json introuvable.")

def extraire_entite(pool_entites):
    return random.choice(pool_entites).copy()

def generer_donnees_admin(pool_entites, nb_par_type=3):
    dataset = []
    types_documents = ["SIRET", "URSSAF", "KBIS", "RIB"]
    formes_juridiques = ["SAS", "SARL", "EURL", "SASU", "SA"]
    
    for type_doc in types_documents:
        for i in range(nb_par_type):
            entite = extraire_entite(pool_entites)
            date_jour = datetime.now()
            
            base_doc = {
                "type_document": type_doc,
                "emetteur": entite,
                "date_edition": date_jour.strftime("%d/%m/%Y"),
                "label_classification": type_doc.lower()
            }
            
            if type_doc == "SIRET":
                base_doc["metadonnees"] = {
                    "code_ape": f"{random.randint(10, 99)}.{random.randint(10, 99)}{random.choice(string.ascii_uppercase)}",
                    "date_immatriculation": fake.date_between(start_date='-10y', end_date='-1y').strftime("%d/%m/%Y"),
                    "activite_principale": fake.catch_phrase()
                }
                
            elif type_doc == "URSSAF":
                base_doc["metadonnees"] = {
                    "code_securite": "".join(random.choices(string.ascii_uppercase + string.digits, k=16)),
                    "compte_urssaf": f"{random.randint(100, 999)} {random.randint(1000000, 9999999)}",
                    "fin_validite": (date_jour + timedelta(days=180)).strftime("%d/%m/%Y")
                }
                
            elif type_doc == "KBIS":
                base_doc["metadonnees"] = {
                    "greffe": f"Tribunal de Commerce de {fake.city().upper()}",
                    "numero_gestion": f"{date_jour.year} B {random.randint(10000, 99999)}",
                    "forme_juridique": random.choice(formes_juridiques),
                    "capital": f"{random.choice([1000, 5000, 10000, 50000, 100000])} Euros",
                    "dirigeant_nom": fake.last_name().upper(),
                    "dirigeant_prenom": fake.first_name(),
                    "dirigeant_naissance": fake.date_of_birth(minimum_age=25, maximum_age=65).strftime("%d/%m/%Y")
                }
                
            elif type_doc == "RIB":
                iban = fake.iban()
                base_doc["metadonnees"] = {
                    "banque": fake.company(),
                    "code_banque": str(random.randint(10000, 30000)),
                    "code_guichet": str(random.randint(10000, 99999)),
                    "numero_compte": "".join(random.choices(string.digits + string.ascii_uppercase, k=11)),
                    "cle_rib": str(random.randint(10, 97)),
                    "iban": " ".join([iban[i:i+4] for i in range(0, len(iban), 4)]),
                    "bic": fake.swift(),
                    "domiciliation": fake.address().replace('\n', ', ')
                }
                
            dataset.append(base_doc)
            
    return dataset

pool_entites_memoire = charger_entites_reference()
dataset_json = generer_donnees_admin(pool_entites_memoire, nb_par_type=2)

with open("dataset_admin.json", "w", encoding="utf-8") as f:
    json.dump(dataset_json, f, indent=4, ensure_ascii=False)