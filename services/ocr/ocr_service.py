import easyocr


class OCRService:
    def __init__(self, languages=None):
        self.languages = languages or ["fr", "en"]
        self.reader = easyocr.Reader(self.languages, gpu=False)

    def extract_text(self, file_path: str) -> str:
        """Extrait le texte d'une image via EasyOCR."""
        results = self.reader.readtext(file_path, detail=0, paragraph=True)
        return "\n".join(results)

    def extract_text_with_confidence(self, file_path: str) -> tuple[str, float]:
        """Extrait le texte et retourne la confiance moyenne (0-100)."""
        results = self.reader.readtext(file_path)
        if not results:
            return "", 0.0
        texts = [r[1] for r in results]
        confidences = [r[2] for r in results]
        avg_confidence = sum(confidences) / len(confidences) * 100
        return "\n".join(texts), round(avg_confidence, 2)
