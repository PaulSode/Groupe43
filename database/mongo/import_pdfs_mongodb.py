import os
from pymongo import MongoClient
import gridfs

# --- CONFIGURATION ---
FOLDER_PDFS = "dataset_pdfs"  
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "pdf_dataset_db"

# --- MONGODB SETUP ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
fs = gridfs.GridFS(db)

# --- FONCTION DE STOCKAGE ---
def save_pdf_to_mongo(file_path):
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()
    file_name = os.path.basename(file_path)
    fs.put(pdf_bytes, filename=file_name)
    print(f"[+] PDF '{file_name}' stocké dans MongoDB ✅")

# --- MAIN ---
def main():
    if not os.path.exists(FOLDER_PDFS):
        print(f"[!] Le dossier '{FOLDER_PDFS}' n'existe pas.")
        return

    for file in os.listdir(FOLDER_PDFS):
        if file.endswith(".pdf"):
            file_path = os.path.join(FOLDER_PDFS, file)
            save_pdf_to_mongo(file_path)

    print("\n[+] Tous les PDFs ont été stockés avec succès.")

if __name__ == "__main__":
    main()
