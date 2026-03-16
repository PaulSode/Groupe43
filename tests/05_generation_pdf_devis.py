import json
import os
import re
from jinja2 import Template
from xhtml2pdf import pisa

def charger_dataset(chemin_fichier="dataset_devis.json"):
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Fichier de données {chemin_fichier} introuvable. Exécuter le script 03.")

def obtenir_dernier_indice_devis(dossier):
    """
    Scanne le dossier pour trouver le numéro de devis le plus élevé.
    Format attendu : D_D-2026-XXXXX_...
    """
    if not os.path.exists(dossier):
        return 0
    
    indices = []
    # Regex capturant les 5 chiffres du pattern D-2026-XXXXX
    motif = re.compile(r"D-2026-(\d{5})")
    
    for fichier in os.listdir(dossier):
        trouve = motif.search(fichier)
        if trouve:
            indices.append(int(trouve.group(1)))
            
    return max(indices) if indices else 0

TEMPLATE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: A4; margin: 1.5cm; }
        body { font-family: Helvetica, sans-serif; font-size: 12px; color: #000; }
        table { width: 100%; }
        .border { border: 0.5px solid #000; padding: 6px; }
        .bg-grey { background-color: #f2f2f2; }
        .right { text-align: right; }
        .bold { font-weight: bold; }
        .signature-box { height: 120px; border: 1px solid #000; padding: 10px; }
        .signature-text { font-size: 16px; color: #00008B; } 
    </style>
</head>
<body>
    <table>
        <tr>
            <td width="50%" valign="top">
                <span class="bold">{{ emetteur.raison_sociale }}</span><br/>
                {{ emetteur.adresse }}<br/>
                SIRET : {{ emetteur.siret }}
            </td>
            <td width="50%" class="right" valign="top">
                <h1 style="margin:0; font-size: 20px;">PROPOSITION COMMERCIALE / DEVIS</h1>
                <span class="bold">N° :</span> {{ metadonnees.numero_devis }}<br/>
                <span class="bold">Date :</span> {{ metadonnees.date_emission }}<br/>
                <span class="bold">Validité :</span> {{ metadonnees.duree_validite_jours }} jours
            </td>
        </tr>
    </table>
    
    <br/><br/><br/>
    
    <table>
        <tr>
            <td width="50%"></td>
            <td width="50%" class="border" valign="top">
                <span class="bold">À l'attention de :</span><br/>
                {{ client.prenom }} {{ client.nom }}<br/>
                {{ client.adresse }}<br/>
                {% if client.siret_societe %}SIRET : {{ client.siret_societe }}{% endif %}
            </td>
        </tr>
    </table>
    
    <br/><br/><br/>
    
    <table class="border">
        <tr class="bg-grey">
            <th class="border" width="45%" align="left">Désignation</th>
            <th class="border right" width="10%">Qté</th>
            <th class="border right" width="22%">PU HT</th>
            <th class="border right" width="23%">Sous-total HT</th>
        </tr>
        {% for item in transactions %}
        <tr>
            <td class="border">{{ item.designation }}</td>
            <td class="border right">{{ item.quantite }}</td>
            <td class="border right">{{ "%.2f"|format(item.prix_unitaire_ht) }} EUR</td>
            <td class="border right">{{ "%.2f"|format(item.sous_total_ht) }} EUR</td>
        </tr>
        {% endfor %}
    </table>
    
    <br/><br/>
    
    <table>
        <tr>
            <td width="55%" valign="top" style="padding-right: 20px;">
                <div class="signature-box">
                    <span class="bold">Approbation du client</span><br/>
                    Mention : "{{ validation.mention_requise }}"<br/><br/>
                    {% if validation.est_signe %}
                    <i>{{ validation.mention_requise }}</i><br/>
                    Signé le : {{ validation.date_signature }}<br/>
                    <br/>
                    <span class="signature-text"><i>[Signature : {{ client.prenom }} {{ client.nom }}]</i></span>
                    {% endif %}
                </div>
            </td>
            <td width="45%" valign="top">
                <table class="border">
                    <tr>
                        <td class="bold border">Total HT</td>
                        <td class="right border">{{ "%.2f"|format(finances.total_ht) }} EUR</td>
                    </tr>
                    <tr>
                        <td class="bold border">TVA (20%)</td>
                        <td class="right border">{{ "%.2f"|format(finances.montant_tva) }} EUR</td>
                    </tr>
                    <tr class="bg-grey">
                        <td class="bold border">Total TTC</td>
                        <td class="right border bold">{{ "%.2f"|format(finances.total_ttc) }} EUR</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

def generer_pdfs_devis_sequentiel():
    dossier_sortie = "devis_pdf"
    os.makedirs(dossier_sortie, exist_ok=True)
    
    # Analyse de l'existant pour déterminer le point de départ
    dernier_indice = obtenir_dernier_indice_devis(dossier_sortie)
    prochain_indice = dernier_indice + 1
    
    donnees_devis = charger_dataset()
    template = Template(TEMPLATE_HTML)
    
    for i, devis in enumerate(donnees_devis):
        # Synchronisation forcée du numéro de document
        indice_actuel = prochain_indice + i
        numero_formate = f"D-2026-{indice_actuel:05d}"
        devis["metadonnees"]["numero_devis"] = numero_formate
        
        date_emission = devis["metadonnees"]["date_emission"]
        nom_fichier = f"D_{numero_formate}_{date_emission}.pdf"
        chemin_complet = os.path.join(dossier_sortie, nom_fichier)
        
        html_rendu = template.render(devis)
        
        with open(chemin_complet, "w+b") as fichier_sortie:
            statut = pisa.CreatePDF(html_rendu, dest=fichier_sortie)
            
        if statut.err:
            print(f"Erreur compilation : {nom_fichier}")
        else:
            print(f"Généré : {nom_fichier} (Indice : {indice_actuel})")

generer_pdfs_devis_sequentiel()