import os
import cv2
import fitz  
from pymongo import MongoClient
import gridfs

# --- CONFIGURATION ---
FOLDER_IMAGES = "../dataset/dataset_images_final"  # dossier des images déjà bruitées
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "pdf_dataset_db"

# --- MONGODB SETUP ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
fs = gridfs.GridFS(db)

# --- FONCTION POUR CONVERTIR IMAGE EN PDF EN MEMOIRE ---
def image_to_pdf_bytes(image_path):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    pdf_doc = fitz.open()
    page = pdf_doc.new_page(width=w, height=h)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pix = fitz.Pixmap(fitz.csRGB, fitz.Image(img_rgb.tobytes(), width=w, height=h))
    page.insert_image(fitz.Rect(0, 0, w, h), pixmap=pix)

    pdf_bytes = pdf_doc.write()
    pdf_doc.close()
    return pdf_bytes

# --- FONCTION DE STOCKAGE ---
def save_pdf_to_mongo(id_document, pdf_bytes, texte_ocr):
    doc = {
        "Id_document": id_document,
        "documents": pdf_bytes,
        "texte_extrait": texte_ocr
    }
    collection.insert_one(doc)
    print(f"[+] Document '{id_document}' stocké avec OCR ✅")

# --- MAIN ---
def main():
    if not os.path.exists(FOLDER_IMAGES):
        print(f"[!] Le dossier '{FOLDER_IMAGES}' n'existe pas.")
        return

    for file in os.listdir(FOLDER_IMAGES):
        if file.endswith(".jpg"):
            pdf_bytes = image_to_pdf_bytes(os.path.join(FOLDER_IMAGES, file))
            pdf_name = os.path.splitext(file)[0] + ".pdf"
            save_pdf_to_mongo(pdf_bytes, pdf_name)

    print("\n[+] Tous les fichiers ont été convertis en PDF et stockés avec succès.")

if __name__ == "__main__":
    main()
