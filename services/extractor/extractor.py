import re
import sys
import os
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from api.models import DocType, ExtractedFields


class DataExtractor:
    """Extrait les données structurées à partir du texte OCR brut."""

    SIRET_PATTERN = r"\b(\d{3}\s?\d{3}\s?\d{3}\s?\d{5})\b"
    SIREN_PATTERN = r"\b(\d{3}\s?\d{3}\s?\d{3})\b"
    TVA_PATTERN = r"\b(FR\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{3})\b"
    DATE_PATTERN = r"\b(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4})\b"
    IBAN_PATTERN = r"\b(FR\s?\d{2}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{3})\b"
    BIC_PATTERN = r"\b([A-Z]{4}FR[A-Z0-9]{2}(?:[A-Z0-9]{3})?)\b"
    NUMERO_DOC_PATTERN = r"(?:facture|invoice|devis)\s*n[°o]?\s*[:\s]?\s*([A-Z0-9\-]+)"

    def extract(self, raw_text: str, doc_type: DocType) -> ExtractedFields:
        """Extrait les champs structurés depuis le texte OCR."""
        text_lower = raw_text.lower()
        fields = ExtractedFields()

        # SIRET (14 chiffres)
        siret_match = re.search(self.SIRET_PATTERN, raw_text)
        if siret_match:
            fields.siret = re.sub(r"\s", "", siret_match.group(1))

        # SIREN (9 chiffres) — déduit du SIRET ou cherché seul
        if not fields.siret:
            siren_match = re.search(self.SIREN_PATTERN, raw_text)
            if siren_match:
                fields.siren = re.sub(r"\s", "", siren_match.group(1))
        else:
            fields.siren = fields.siret[:9]

        # TVA intracommunautaire
        tva_match = re.search(self.TVA_PATTERN, raw_text, re.IGNORECASE)
        if tva_match:
            fields.tva_intracom = re.sub(r"\s", "", tva_match.group(1)).upper()

        # Montants HT / TTC (recherche contextuelle par mot-clé)
        fields.montant_ht = self._find_amount(raw_text, ["ht", "hors taxe", "h.t"])
        fields.montant_ttc = self._find_amount(
            raw_text, ["ttc", "toutes taxes", "t.t.c", "net à payer", "total"]
        )

        # Taux TVA
        tva_rate = re.search(r"(?:tva|taux)\s*[:\s]?\s*(\d{1,2}[.,]?\d{0,2})\s*%", text_lower)
        if tva_rate:
            fields.taux_tva = tva_rate.group(1).replace(",", ".") + "%"

        # Dates
        dates = re.findall(self.DATE_PATTERN, raw_text)
        if dates:
            fields.date_emission = self._pick_date(raw_text, dates, "emission")
            if doc_type in (DocType.ATTESTATION_VIGILANCE, DocType.ATTESTATION_SIRET, DocType.KBIS):
                fields.date_expiration = self._pick_date(raw_text, dates, "expiration")

        # Numéro de document
        if doc_type in (DocType.FACTURE, DocType.DEVIS):
            num_match = re.search(self.NUMERO_DOC_PATTERN, text_lower)
            if num_match:
                fields.numero_document = num_match.group(1).upper()

        # IBAN / BIC
        iban_match = re.search(self.IBAN_PATTERN, raw_text, re.IGNORECASE)
        if iban_match:
            fields.iban = re.sub(r"\s", "", iban_match.group(1)).upper()

        bic_match = re.search(self.BIC_PATTERN, raw_text)
        if bic_match:
            fields.bic = bic_match.group(1)

        return fields

    def _find_amount(self, text: str, keywords: list) -> Optional[str]:
        """Cherche un montant proche d'un mot-clé contextuel."""
        for kw in keywords:
            pattern = rf"(?:{kw})\s*[:\s]?\s*(\d[\d\s]*[.,]\d{{2}})\s*[€E]?"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).replace(" ", "").replace(",", ".")
        return None

    def _pick_date(self, text: str, dates: list, context: str) -> Optional[str]:
        """Sélectionne la date la plus pertinente selon le contexte."""
        text_lower = text.lower()

        if context == "emission":
            for kw in ["date", "émission", "emission", "établi", "etabli", "du", "le", "facture du", "en date du"]:
                pattern = rf"{kw}\s*[:\s]?\s*(\d{{1,2}}[/.\-]\d{{1,2}}[/.\-]\d{{2,4}})"
                m = re.search(pattern, text_lower)
                if m:
                    return m.group(1)

        if context == "expiration":
            for kw in ["expir", "validit", "valable jusqu", "fin de validit", "jusqu'au", "date limite"]:
                pattern = rf"{kw}\s*[:\s]?\s*(\d{{1,2}}[/.\-]\d{{1,2}}[/.\-]\d{{2,4}})"
                m = re.search(pattern, text_lower)
                if m:
                    return m.group(1)

        return dates[0] if dates else None
