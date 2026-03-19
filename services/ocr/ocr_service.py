import os
import tempfile
import easyocr
import fitz  # PyMuPDF


class OCRService:
    def __init__(self, languages=None):
        self.languages = languages or ["fr", "en"]
        self.reader = easyocr.Reader(self.languages, gpu=False)

    def extract_text(self, file_path: str) -> str:
        """Extrait le texte d'un fichier (image ou PDF) via EasyOCR."""
        image_paths = self._to_images(file_path)
        all_text = []
        for img_path in image_paths:
            results = self.reader.readtext(img_path, detail=0, paragraph=True)
            all_text.extend(results)
        self._cleanup_temp(image_paths, file_path)
        return "\n".join(all_text)

    def extract_text_with_confidence(self, file_path: str) -> tuple[str, float]:
        """Extrait le texte et retourne la confiance moyenne (0-100)."""
        image_paths = self._to_images(file_path)
        all_texts = []
        all_confidences = []
        for img_path in image_paths:
            results = self.reader.readtext(img_path)
            if results:
                all_texts.extend(r[1] for r in results)
                all_confidences.extend(r[2] for r in results)
        self._cleanup_temp(image_paths, file_path)
        if not all_confidences:
            return "", 0.0
        avg_confidence = sum(all_confidences) / len(all_confidences) * 100
        return "\n".join(all_texts), round(avg_confidence, 2)

    def _to_images(self, file_path: str) -> list[str]:
        """Convertit un PDF en images PNG. Retourne tel quel si c'est déjà une image."""
        if not file_path.lower().endswith(".pdf"):
            return [file_path]

        doc = fitz.open(file_path)
        image_paths = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=300)
            tmp = tempfile.NamedTemporaryFile(suffix=f"_p{page_num}.png", delete=False)
            pix.save(tmp.name)
            image_paths.append(tmp.name)
            tmp.close()
        doc.close()
        return image_paths

    @staticmethod
    def _cleanup_temp(image_paths: list[str], original_path: str):
        """Supprime les fichiers temporaires créés pour les PDF."""
        for path in image_paths:
            if path != original_path and os.path.exists(path):
                os.remove(path)
