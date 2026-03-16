import json
import os
import re
from jinja2 import Template
from xhtml2pdf import pisa

# --- CONFIGURATION DES RÉPERTOIRES ---
PATHS = {
    "FACTURE": "factures_pdf",
    "DEVIS": "devis_pdf",
    "ADMIN": "admin_pdf"
}

def charger_dataset(chemin="dataset_global.json"):
    if not os.path.exists(chemin):
        raise RuntimeError(f"Source {chemin} introuvable.")
    with open(chemin, "r", encoding="utf-8") as f:
        return json.load(f)

def obtenir_dernier_indice(dossier, prefixe_regex):
    if not os.path.exists(dossier): return 0
    indices = []
    motif = re.compile(prefixe_regex)
    for f in os.listdir(dossier):
        trouve = motif.search(f)
        if trouve: indices.append(int(trouve.group(1)))
    return max(indices) if indices else 0

# --- MATRICES HTML ---

TEMPLATE_FACTURE = """
<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><style>@page { size: A4; margin: 1.5cm; } body { font-family: Helvetica; font-size: 12px; } table { width: 100%; } .border { border: 0.5px solid #000; padding: 6px; } .bg-grey { background-color: #f2f2f2; } .right { text-align: right; } .bold { font-weight: bold; }</style></head>
<body>
    <table><tr>
        <td width="50%" valign="top"><span class="bold">{{ emetteur.nom }}</span><br/>{{ emetteur.adresse }}<br/>SIRET : {{ emetteur.siret }}</td>
        <td width="50%" class="right" valign="top"><h1 style="margin:0; font-size: 20px;">FACTURE</h1><span class="bold">N° :</span> {{ metadonnees.numero }}<br/><span class="bold">Date :</span> {{ metadonnees.date_emission }}</td>
    </tr></table><br/><br/>
    <table><tr><td width="50%"></td><td width="50%" class="border" valign="top"><span class="bold">Facturé à :</span><br/>{{ client.prenom }} {{ client.nom }}<br/>{{ client.adresse }}</td></tr></table><br/><br/>
    <table class="border"><tr class="bg-grey"><th class="border" align="left">Désignation</th><th class="border right">Qté</th><th class="border right">PU HT</th><th class="border right">Total HT</th></tr>
    {% for item in transactions %}<tr><td class="border">{{ item.designation }}</td><td class="border right">{{ item.quantite }}</td><td class="border right">{{ "%.2f"|format(item.prix_unitaire_ht) }} EUR</td><td class="border right">{{ "%.2f"|format(item.sous_total_ht) }} EUR</td></tr>{% endfor %}</table><br/>
    <table align="right" width="40%" class="border"><tr><td class="bold">TOTAL TTC</td><td class="right bold">{{ "%.2f"|format(finances.total_ttc) }} EUR</td></tr></table>
</body></html>
"""

TEMPLATE_DEVIS = """
<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><style>@page { size: A4; margin: 1.5cm; } body { font-family: Helvetica; font-size: 12px; } table { width: 100%; } .border { border: 0.5px solid #000; padding: 6px; } .right { text-align: right; } .bold { font-weight: bold; } .signature-box { height: 110px; border: 1px solid #000; padding: 10px; }</style></head>
<body>
    <table><tr>
        <td width="50%" valign="top"><span class="bold">{{ emetteur.nom }}</span><br/>{{ emetteur.adresse }}<br/>SIRET : {{ emetteur.siret }}</td>
        <td width="50%" class="right" valign="top"><h1 style="margin:0; font-size: 20px;">DEVIS</h1><span class="bold">N° :</span> {{ metadonnees.numero }}<br/><span class="bold">Date :</span> {{ metadonnees.date_emission }}</td>
    </tr></table><br/><br/>
    <table class="border"><tr style="background-color:#f2f2f2"><th class="border" align="left">Description des prestations</th><th class="border right">Total HT</th></tr>
    {% for item in transactions %}<tr><td class="border">{{ item.designation }}</td><td class="border right">{{ "%.2f"|format(item.sous_total_ht) }} EUR</td></tr>{% endfor %}</table><br/>
    <table><tr><td width="55%" valign="top"><div class="signature-box"><b>Bon pour accord :</b><br/>{% if validation.est_signe %}<i style="color:darkblue; font-size:14px;">Le {{ validation.date_signature }}<br/>[Signature client : {{ client.prenom }}]</i>{% endif %}</div></td>
    <td width="45%"><table class="border"><tr><td class="bold">TOTAL TTC</td><td class="right bold">{{ "%.2f"|format(finances.total_ttc) }} EUR</td></tr></table></td></tr></table>
</body></html>
"""

TEMPLATE_KBIS = """
<!DOCTYPE html><html><head><style>body { font-family: Helvetica; font-size: 9px; } .title { text-align: center; font-size: 14px; font-weight: bold; border-bottom: 1px solid black; } td { padding: 6px; border-bottom: 0.5px solid #ccc; }</style></head>
<body>
    <div class="title">EXTRAIT D'IMMATRICULATION (KBIS)<br/>au Registre du Commerce et des Sociétés</div><br/>
    <b>{{ metadonnees.greffe }}</b><br/><br/>
    <table width="100%">
        <tr><td width="35%"><b>Numéro d'identification</b></td><td width="65%">{{ emetteur.siret[:9] }} RCS {{ metadonnees.greffe }}</td></tr>
        <tr><td><b>Dénomination sociale</b></td><td>{{ emetteur.nom }}</td></tr>
        <tr><td><b>Forme juridique</b></td><td>{{ metadonnees.forme_juridique }}</td></tr>
        <tr><td><b>Capital social</b></td><td>{{ metadonnees.capital }}</td></tr>
        <tr><td><b>Siège social</b></td><td>{{ emetteur.adresse }}</td></tr>
    </table>
</body></html>
"""

TEMPLATE_RIB = """
<!DOCTYPE html><html><head><style>body { font-family: Helvetica; font-size: 11px; } .border { border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold; } .data { border: 1px solid #000; padding: 10px; text-align: center; font-family: Courier; }</style></head>
<body>
    <h2 style="border-bottom: 1px solid #000;">Relevé d'Identité Bancaire (RIB)</h2>
    <b>Titulaire du compte :</b> {{ emetteur.nom }}<br/>{{ emetteur.adresse }}<br/><br/>
    <b>Domiciliation :</b> {{ metadonnees.banque }}<br/><br/>
    <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td width="20%" class="border">Code Banque</td><td width="20%" class="border">Guichet</td><td width="40%" class="border">N° de Compte</td><td width="20%" class="border">Clé</td></tr>
        <tr><td class="data">{{ metadonnees.code_banque }}</td><td class="data">{{ metadonnees.code_guichet }}</td><td class="data">{{ metadonnees.numero_compte }}</td><td class="data">{{ metadonnees.cle_rib }}</td></tr>
    </table><br/>
    <table width="100%">
        <tr><td width="20%"><b>IBAN :</b></td><td width="80%" style="font-family: Courier; font-size: 14px;">{{ metadonnees.iban }}</td></tr>
        <tr><td><b>BIC :</b></td><td style="font-family: Courier; font-size: 14px;">{{ metadonnees.bic }}</td></tr>
    </table>
</body></html>
"""

TEMPLATE_URSSAF = """
<!DOCTYPE html><html><head><style>body { font-family: Helvetica; font-size: 10px; } .header { border-bottom: 2px solid #000; padding-bottom: 10px; }</style></head>
<body>
    <div class="header"><h1 style="font-size:16px;">URSSAF - Attestation de fourniture des déclarations sociales</h1></div><br/><br/>
    <b>Raison sociale :</b> {{ emetteur.nom }}<br/><b>SIRET :</b> {{ emetteur.siret }}<br/><br/>
    <p>Nous certifions que l'entreprise désignée ci-dessus est à jour de ses obligations sociales au {{ date_edition }}.</p>
    <table style="border: 1px dashed #000; width: 100%;"><tr><td style="padding: 10px;">
        <b>Code de sécurité d'authentification :</b><br/>
        <span style="font-size:14px; font-family: Courier;">{{ metadonnees.code_securite }}</span>
    </td></tr></table>
</body></html>
"""

TEMPLATE_SIRET = """
<!DOCTYPE html><html><head><style>body { font-family: Helvetica; font-size: 11px; } .box { border: 1px solid black; padding: 15px; }</style></head>
<body>
    <div style="font-weight:bold; font-size:24px;">INSEE</div><br/><br/>
    <div style="text-align:center; font-size:18px; font-weight:bold;">Avis de situation au répertoire Sirene</div><br/><br/>
    <div class="box">
        <b>Identifiant SIRET :</b> {{ emetteur.siret }}<br/><br/>
        <b>Dénomination :</b> {{ emetteur.nom }}<br/><br/>
        <b>Adresse :</b> {{ emetteur.adresse }}<br/><br/>
        <b>Activité Principale (APE) :</b> {{ metadonnees.ape }} - {{ metadonnees.activite }}<br/><br/>
        <b>Date d'immatriculation :</b> {{ metadonnees.immatriculation }}
    </div>
    <br/><i>Document généré le {{ date_edition }}</i>
</body></html>
"""

# --- LOGIQUE DE RENDU ---

def generer_tous_les_pdfs():
    # Création des dossiers de sortie
    for p in PATHS.values(): os.makedirs(p, exist_ok=True)
    
    data = charger_dataset()
    
    # Mapping des templates administratifs
    T_ADMIN = {
        "SIRET": TEMPLATE_SIRET,
        "URSSAF": TEMPLATE_URSSAF,
        "KBIS": TEMPLATE_KBIS,
        "RIB": TEMPLATE_RIB
    }
    
    # Initialisation des compteurs physiques
    idx_f = obtenir_dernier_indice(PATHS["FACTURE"], r"F-2026-(\d{5})") + 1
    idx_d = obtenir_dernier_indice(PATHS["DEVIS"], r"D-2026-(\d{5})") + 1
    compteurs_admin = {"SIRET": 1, "URSSAF": 1, "KBIS": 1, "RIB": 1}

    for doc in data:
        t = doc["type_document"]
        html_content = ""
        output_path = ""
        
        if t == "FACTURE":
            num = f"F-2026-{idx_f:05d}"
            doc["metadonnees"]["numero"] = num
            html_content = Template(TEMPLATE_FACTURE).render(doc)
            name = f"F_{num}_{doc['metadonnees']['date_emission']}.pdf"
            output_path = os.path.join(PATHS["FACTURE"], name)
            idx_f += 1
            
        elif t == "DEVIS":
            num = f"D-2026-{idx_d:05d}"
            doc["metadonnees"]["numero"] = num
            html_content = Template(TEMPLATE_DEVIS).render(doc)
            name = f"D_{num}_{doc['metadonnees']['date_emission']}.pdf"
            output_path = os.path.join(PATHS["DEVIS"], name)
            idx_d += 1
            
        elif t in T_ADMIN:
            html_content = Template(T_ADMIN[t]).render(doc)
            name = f"{t}_{compteurs_admin[t]}_{doc['emetteur']['siret']}.pdf"
            output_path = os.path.join(PATHS["ADMIN"], name)
            compteurs_admin[t] += 1
        
        # Génération du PDF si un template a été trouvé
        if html_content and output_path:
            with open(output_path, "w+b") as f_out:
                pisa.CreatePDF(html_content, dest=f_out)
            print(f"Généré avec succès : {output_path}")

if __name__ == "__main__":
    generer_tous_les_pdfs()