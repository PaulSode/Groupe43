import json
import os
from jinja2 import Template
from xhtml2pdf import pisa

def charger_dataset(chemin_fichier="dataset_factures.json"):
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Fichier de données {chemin_fichier} introuvable.")

# Gabarit rétrogradé : structure tabulaire obligatoire pour contourner l'absence de moteur CSS moderne
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
                <h1 style="margin:0; font-size: 20px;">FACTURE</h1>
                <span class="bold">N° :</span> {{ metadonnees.numero_facture }}<br/>
                <span class="bold">Date :</span> {{ metadonnees.date_emission }}
            </td>
        </tr>
    </table>
    
    <br/><br/><br/>
    
    <table>
        <tr>
            <td width="50%"></td>
            <td width="50%" class="border" valign="top">
                <span class="bold">Facturé à :</span><br/>
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
            <td width="55%"></td>
            <td width="45%">
                <table class="border">
                    <tr>
                        <td class="bold border">Total HT</td>
                        <td class="right border">{{ "%.2f"|format(finances.total_ht) }} EUR</td>
                    </tr>
                    <tr>
                        <td class="bold border">TVA ({{ (finances.taux_tva * 100)|int }}%)</td>
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

def generer_pdfs_xhtml2pdf():
    dossier_sortie = "factures_pdf"
    os.makedirs(dossier_sortie, exist_ok=True)
    
    donnees_factures = charger_dataset()
    template = Template(TEMPLATE_HTML)
    
    for facture in donnees_factures:
        html_rendu = template.render(facture)
        
        numero_facture = facture["metadonnees"]["numero_facture"]
        date_emission = facture["metadonnees"]["date_emission"]
        nom_fichier = f"F_{numero_facture}_{date_emission}.pdf"
        chemin_complet = os.path.join(dossier_sortie, nom_fichier)
        
        # Flux binaire d'écriture exigé par xhtml2pdf (w+b)
        with open(chemin_complet, "w+b") as fichier_sortie:
            statut = pisa.CreatePDF(html_rendu, dest=fichier_sortie)
            
        if statut.err:
            print(f"Échec de la compilation géométrique : {nom_fichier}")
        else:
            print(f"Compilation réussie : {chemin_complet}")

generer_pdfs_xhtml2pdf()