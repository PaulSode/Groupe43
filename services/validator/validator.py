from datetime import datetime, date
from typing import List
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from api.models import ExtractionResult, VerificationReport, Anomaly


class DocumentValidator:
    """Vérifie la cohérence inter-documents."""

    def validate(self, documents: List[ExtractionResult]) -> VerificationReport:
        anomalies: List[Anomaly] = []

        anomalies.extend(self._check_siret_coherence(documents))
        anomalies.extend(self._check_expiration_dates(documents))
        anomalies.extend(self._check_tva_coherence(documents))
        anomalies.extend(self._check_montant_coherence(documents))

        return VerificationReport(
            total_documents=len(documents),
            anomalies=anomalies,
            is_coherent=len([a for a in anomalies if a.severity == "error"]) == 0,
        )

    def _check_siret_coherence(self, docs: List[ExtractionResult]) -> List[Anomaly]:
        """Détecte les incohérences de SIRET entre facture et attestation."""
        anomalies = []
        siret_map: dict[str, list[str]] = {}

        for doc in docs:
            if doc.fields.siret:
                siret_map.setdefault(doc.fields.siret, []).append(doc.filename)

        if len(siret_map) > 1:
            all_files = [f for files in siret_map.values() for f in files]
            sirets_found = ", ".join(siret_map.keys())
            anomalies.append(Anomaly(
                severity="error",
                category="SIRET_INCOHERENCE",
                message=(
                    f"Incohérence SIRET détectée : {len(siret_map)} numéros SIRET "
                    f"différents trouvés ({sirets_found}). "
                    f"Vérifiez que tous les documents concernent la même entité."
                ),
                documents=all_files,
            ))

        for doc in docs:
            if doc.fields.siret and not self._validate_siret(doc.fields.siret):
                anomalies.append(Anomaly(
                    severity="warning",
                    category="SIRET_FORMAT",
                    message=f"Le SIRET {doc.fields.siret} ne passe pas la validation Luhn.",
                    documents=[doc.filename],
                ))

        return anomalies

    def _check_expiration_dates(self, docs: List[ExtractionResult]) -> List[Anomaly]:
        """Détecte les documents dont la date d'expiration est dépassée."""
        anomalies = []
        today = date.today()

        for doc in docs:
            if doc.fields.date_expiration:
                exp_date = self._parse_date(doc.fields.date_expiration)
                if exp_date and exp_date < today:
                    days_expired = (today - exp_date).days
                    anomalies.append(Anomaly(
                        severity="error",
                        category="DATE_EXPIREE",
                        message=(
                            f"Le document '{doc.filename}' ({doc.doc_type.value}) "
                            f"est expiré depuis {days_expired} jours "
                            f"(expiration : {doc.fields.date_expiration})."
                        ),
                        documents=[doc.filename],
                    ))
                elif exp_date:
                    days_left = (exp_date - today).days
                    if days_left <= 30:
                        anomalies.append(Anomaly(
                            severity="warning",
                            category="DATE_EXPIRATION_PROCHE",
                            message=(
                                f"Le document '{doc.filename}' expire dans {days_left} jours "
                                f"(expiration : {doc.fields.date_expiration})."
                            ),
                            documents=[doc.filename],
                        ))

        return anomalies

    def _check_tva_coherence(self, docs: List[ExtractionResult]) -> List[Anomaly]:
        """Vérifie la cohérence des numéros TVA entre documents."""
        anomalies = []
        tva_map: dict[str, list[str]] = {}

        for doc in docs:
            if doc.fields.tva_intracom:
                tva_map.setdefault(doc.fields.tva_intracom, []).append(doc.filename)

        if len(tva_map) > 1:
            all_files = [f for files in tva_map.values() for f in files]
            anomalies.append(Anomaly(
                severity="warning",
                category="TVA_INCOHERENCE",
                message=(
                    f"Plusieurs numéros de TVA intracommunautaire détectés : "
                    f"{', '.join(tva_map.keys())}."
                ),
                documents=all_files,
            ))

        return anomalies

    def _check_montant_coherence(self, docs: List[ExtractionResult]) -> List[Anomaly]:
        """Vérifie la cohérence HT/TTC avec le taux TVA si disponible."""
        anomalies = []

        for doc in docs:
            f = doc.fields
            if f.montant_ht and f.montant_ttc and f.taux_tva:
                try:
                    ht = float(f.montant_ht)
                    ttc = float(f.montant_ttc)
                    taux = float(f.taux_tva.replace("%", ""))
                    expected_ttc = round(ht * (1 + taux / 100), 2)
                    diff = abs(expected_ttc - ttc)
                    if diff > 0.02:
                        anomalies.append(Anomaly(
                            severity="warning",
                            category="MONTANT_INCOHERENCE",
                            message=(
                                f"Incohérence montant dans '{doc.filename}' : "
                                f"HT={ht}€ × TVA {taux}% = {expected_ttc}€ TTC attendu, "
                                f"mais {ttc}€ TTC trouvé (écart : {diff:.2f}€)."
                            ),
                            documents=[doc.filename],
                        ))
                except (ValueError, TypeError):
                    pass

        return anomalies

    @staticmethod
    def _validate_siret(siret: str) -> bool:
        """Validation Luhn du SIRET."""
        if len(siret) != 14 or not siret.isdigit():
            return False
        total = 0
        for i, c in enumerate(siret):
            n = int(c)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0

    @staticmethod
    def _parse_date(date_str: str):
        """Parse une date dans les formats courants français."""
        formats = ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y"]
        cleaned = date_str.strip()
        for fmt in formats:
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue
        return None
