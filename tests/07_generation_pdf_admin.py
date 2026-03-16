import json
import os
from jinja2 import Template
from xhtml2pdf import pisa

def charger_dataset(chemin="dataset_admin.json"):
    with open(chemin, "r", encoding="utf-8") as f:
        return json.load(f)

# Matrice structurelle : Attestation SIRET (Avis de situation au répertoire Sirene)
TEMPLATE_SIRET = """
<!DOCTYPE html>
<html>
<head><style>body { font-family: Helvetica; font-size: 11px; } .title { font-size: 18px; font-weight: bold; text-align: center; } .box { border: 1px solid black; padding: 15px; }</style></head>
<body>
    <div style="font-weight:bold; font-size:24px;">INSEE</div>
    <br/><br/>
    <div class="title">Avis de situation au répertoire Sirene</div>
    <br/><br/><br/>
    <div class="box">
        <b>Identifiant SIRET :</b> {{ emetteur.siret }}<br/><br/>
        <b>Raison sociale :</b> {{ emetteur.raison_sociale }}<br/><br/>
        <b>Adresse :</b> {{ emetteur.adresse }}<br/><br/>
        <b>Activité Principale Exercée (APE) :</b> {{ metadonnees.code_ape }} - {{ metadonnees.activite_principale }}<br/><br/>
        <b>Date d'immatriculation :</b> {{ metadonnees.date_immatriculation }}
    </div>
    <br/><br/>
    <i>Avis généré le {{ date_edition }}</i>
</body>
</html>
"""

# Matrice structurelle : Attestation URSSAF (Forte densité textuelle légale)
TEMPLATE_URSSAF = """
<!DOCTYPE html>
<html>
<head><style>body { font-family: Helvetica; font-size: 10px; } .header { border-bottom: 2px solid #000; padding-bottom: 10px; }</style></head>
<body>
    <div class="header">
        <h1 style="font-size:16px;">URSSAF - Attestation de fourniture des déclarations sociales</h1>
    </div>
    <br/><br/>
    <b>Compte cotisant :</b> {{ metadonnees.compte_urssaf }}<br/>
    <b>Raison sociale :</b> {{ emetteur.raison_sociale }}<br/>
    <b>SIRET :</b> {{ emetteur.siret }}<br/>
    <br/><br/>
    <p>Nous certifions que l'entreprise désignée ci-dessus est à jour de ses obligations de déclaration et de paiement des cotisations de Sécurité sociale au {{ date_edition }}.</p>
    <p>Cette attestation est valable jusqu'au <b>{{ metadonnees.fin_validite }}</b>.</p>
    <br/><br/><br/>
    <table style="border: 1px dashed #000; width: 100%;">
        <tr>
            <td style="padding: 10px;">
                <b>Code de sécurité d'authentification :</b><br/>
                <span style="font-size:14px; font-family: Courier;">{{ metadonnees.code_securite }}</span><br/>
                <i>À vérifier sur urssaf.fr</i>
            </td>
        </tr>
    </table>
</body>
</html>
"""

# Matrice structurelle : Extrait Kbis (Densité tabulaire maximale, divisions verticales)
TEMPLATE_KBIS = """
<!DOCTYPE html>
<html>
<head><style>body { font-family: Helvetica; font-size: 9px; } .kbis-title { text-align: center; font-size: 14px; font-weight: bold; border-bottom: 1px solid black; } td { padding: 4px; border-bottom: 0.5px solid #ccc; }</style></head>
<body>
    <div class="kbis-title">
        RÉPUBLIQUE FRANÇAISE<br/>
        EXTRAIT D'IMMATRICULATION PRINCIPALE AU REGISTRE DU COMMERCE ET DES SOCIÉTÉS<br/>
        à jour au {{ date_edition }}
    </div>
    <br/>
    <b>{{ metadonnees.greffe }}</b><br/><br/>
    <table width="100%">
        <tr>
            <td width="30%"><b>Identification</b></td>
            <td width="70%">
                N° d'identification : {{ emetteur.siret[:9] }} RCS<br/>
                N° de gestion : {{ metadonnees.numero_gestion }}
            </td>
        </tr>
        <tr>
            <td><b>Dénomination sociale</b></td>
            <td>{{ emetteur.raison_sociale }}</td>
        </tr>
        <tr>
            <td><b>Forme juridique</b></td>
            <td>{{ metadonnees.forme_juridique }}</td>
        </tr>
        <tr>
            <td><b>Capital social</b></td>
            <td>{{ metadonnees.capital }}</td>
        </tr>
        <tr>
            <td><b>Adresse du siège</b></td>
            <td>{{ emetteur.adresse }}</td>
        </tr>
        <tr>
            <td><b>Dirigeant(s)</b></td>
            <td>
                Nom : {{ metadonnees.dirigeant_nom }}<br/>
                Prénom : {{ metadonnees.dirigeant_prenom }}<br/>
                Né(e) le : {{ metadonnees.dirigeant_naissance }}
            </td>
        </tr>
    </table>
</body>
</html>
"""

# Matrice structurelle : RIB (Grille à 4 compartiments)
TEMPLATE_RIB = """
<!DOCTYPE html>
<html>
<head><style>body { font-family: Helvetica; font-size: 11px; } .border { border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold; } .data { border: 1px solid #000; padding: 10px; text-align: center; font-family: Courier; }</style></head>
<body>
    <h2 style="border-bottom: 1px solid #000;">Relevé d'Identité Bancaire (RIB)</h2>
    <b>Titulaire du compte :</b> {{ emetteur.raison_sociale }}<br/>
    {{ emetteur.adresse }}<br/><br/>
    <b>Domiciliation :</b> {{ metadonnees.banque }}<br/>
    {{ metadonnees.domiciliation }}<br/><br/>
    
    <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td width="20%" class="border">Code Banque</td>
            <td width="20%" class="border">Code Guichet</td>
            <td width="40%" class="border">N° de Compte</td>
            <td width="20%" class="border">Clé RIB</td>
        </tr>
        <tr>
            <td class="data">{{ metadonnees.code_banque }}</td>
            <td class="data">{{ metadonnees.code_guichet }}</td>
            <td class="data">{{ metadonnees.numero_compte }}</td>
            <td class="data">{{ metadonnees.cle_rib }}</td>
        </tr>
    </table>
    <br/><br/>
    <table width="100%">
        <tr>
            <td width="25%"><b>IBAN :</b></td>
            <td width="75%" style="font-family: Courier; font-size: 14px;">{{ metadonnees.iban }}</td>
        </tr>
        <tr>
            <td><b>BIC :</b></td>
            <td style="font-family: Courier; font-size: 14px;">{{ metadonnees.bic }}</td>
        </tr>
    </table>
</body>
</html>
"""

def generer_pdfs():
    dossier_sortie = "admin_pdf"
    os.makedirs(dossier_sortie, exist_ok=True)
    donnees = charger_dataset()
    
    mapping_templates = {
        "SIRET": TEMPLATE_SIRET,
        "URSSAF": TEMPLATE_URSSAF,
        "KBIS": TEMPLATE_KBIS,
        "RIB": TEMPLATE_RIB
    }
    
    compteurs = {"SIRET": 1, "URSSAF": 1, "KBIS": 1, "RIB": 1}
    
    for doc in donnees:
        t_doc = doc["type_document"]
        template = Template(mapping_templates[t_doc])
        html_rendu = template.render(doc)
        
        nom_fichier = f"{t_doc}_{compteurs[t_doc]}_{doc['emetteur']['siret']}.pdf"
        chemin_complet = os.path.join(dossier_sortie, nom_fichier)
        
        with open(chemin_complet, "w+b") as fichier_sortie:
            statut = pisa.CreatePDF(html_rendu, dest=fichier_sortie)
            
        if statut.err:
            print(f"Échec compilation : {nom_fichier}")
        else:
            print(f"Généré : {chemin_complet}")
            
        compteurs[t_doc] += 1

generer_pdfs()