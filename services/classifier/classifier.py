import re
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from api.models import DocType


class DocumentClassifier:
    """Classifie un document à partir du texte OCR brut."""
    DOC_TYPE_PATTERNS = {
        DocType.FACTURE: [
            r"facture",
            r"invoice",
            r"n[°o]\s*de\s*facture",
            r"facture\s*n[°o]",
        ],
        DocType.DEVIS: [
            r"devis",
            r"proposition\s+commerciale",
            r"offre\s+de\s+prix",
        ],
        DocType.ATTESTATION_SIRET: [
            r"avis\s+de\s+situation",
            r"r[ée]pertoire\s+sir[eè]ne",
            r"attestation\s+siret",
            r"inscription\s+au\s+r[ée]pertoire",
        ],
        DocType.ATTESTATION_VIGILANCE: [
            r"attestation\s+de\s+vigilance",
            r"urssaf",
            r"obligations\s+sociales",
        ],
        DocType.KBIS: [
            r"extrait\s+kbis",
            r"k\s*bis",
            r"registre\s+du\s+commerce",
            r"greffe\s+du\s+tribunal",
        ],
        DocType.RIB: [
            r"relev[ée]\s+d.identit[ée]\s+bancaire",
            r"\brib\b",
            r"\biban\b",
            r"coordonn[ée]es\s+bancaires",
        ],
    }

    def classify(self, raw_text: str) -> DocType:
        """Retourne le type de document le plus probable."""
        text_lower = raw_text.lower()
        scores = {}
        for dtype, patterns in self.DOC_TYPE_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, text_lower))
            if score > 0:
                scores[dtype] = score

        if not scores:
            return DocType.INCONNU
        return max(scores, key=scores.get)
