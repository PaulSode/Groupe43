import requests
import sys
import json
import time

def extraire_donnees_api_diversifiees():
    secteurs = ["boulangerie", "informatique", "restauration", "transport", "maconnerie", "conseil"]
    resultats_par_secteur = 6
    entites_globales = []
    sirets_deja_extraits = set()

    for domaine in secteurs:
        url = f"https://recherche-entreprises.api.gouv.fr/search?q={domaine}&per_page={resultats_par_secteur}"
        try:
            reponse = requests.get(url, timeout=10)
            reponse.raise_for_status()
            time.sleep(0.2) 
            donnees = reponse.json()
            
            for ent in donnees.get("results", []):
                siege = ent.get("siege", {})
                siret = siege.get("siret")
                
                if siret and siret not in sirets_deja_extraits:
                    entites_globales.append({
                        "siret": siret, 
                        "nom": ent.get("nom_complet", "Nom Inconnu"), 
                        "adresse": siege.get("adresse", "Adresse Inconnue"),
                        "code_ape": ent.get("activite_principale", "99.99Z"),
                        "activite_principale": ent.get("activite_principale_libelle", "Activité non spécifiée"),
                        "date_immatriculation": ent.get("date_creation", "2020-01-01")
                    })
                    sirets_deja_extraits.add(siret)
        except Exception as e:
            print(f"Erreur sur le secteur {domaine}: {e}")
            continue
            
    return entites_globales

# --- CORRECTION DE L'APPEL ---
# On stocke le résultat de la fonction dans une variable locale au script
resultat_final = extraire_donnees_api_diversifiees()

with open("entites_reference.json", "w", encoding="utf-8") as f:
    json.dump(resultat_final, f, indent=4, ensure_ascii=False)

print("-" * 30)
# Utilisation de la variable stockée pour éviter le NameError
print(f"Extraction terminée : {len(resultat_final)} entités uniques sauvegardées.")