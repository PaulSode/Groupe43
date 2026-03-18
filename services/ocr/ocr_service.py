import easyocr


class OCRService:
    def __init__(self, languages=None):
        self.languages = languages or ["fr", "en"]
        self.reader = easyocr.Reader(self.languages, gpu=False)

    def extract_text(self, file_path: str) -> str:
        """Extrait le texte d'une image via EasyOCR."""
        results = self.reader.readtext(file_path, detail=0, paragraph=True)
        return "\n".join(results)
