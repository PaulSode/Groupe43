import requests
import sys
import json

def extraire_donnees_api():
    url = "https://recherche-entreprises.api.gouv.fr/search?q=boulangerie&per_page=10"
    
    try:
        reponse = requests.get(url, timeout=10)
        reponse.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Échec critique de l'appel API : {e}")
        sys.exit(1)
        
    donnees = reponse.json()
    entites = []
    
    for entreprise in donnees.get("results", []):
        siege = entreprise.get("siege", {})
        siret = siege.get("siret")
        nom = entreprise.get("nom_complet", "Nom Inconnu")
        adresse = siege.get("adresse", "Adresse Inconnue")
        
        if siret:
            entites.append({
                "siret": siret, 
                "nom": nom, 
                "adresse": adresse
            })
            
    return entites

entites_extraites = extraire_donnees_api()

with open("entites_reference.json", "w", encoding="utf-8") as f:
    json.dump(entites_extraites, f, indent=4, ensure_ascii=False)

print(f"Extraction terminée : {len(entites_extraites)} entités sauvegardées.")

# ['47845579305205', '40305211102616', '63850296300082', '44284394200115', '39440693800149', '48006563000018', '83533411100019', '78947258600013', '43508926300014', '52344029500013']