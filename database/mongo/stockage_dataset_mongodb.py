import os
from pymongo import MongoClient

# --- CONFIGURATION ---
FOLDER_IMAGES = "../dataset/dataset_images_final"  # dossier des images déjà bruitées
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "Data_Mongodb"
COLLECTION_NAME = "images_raw"

# --- MONGODB SETUP ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --- FONCTION DE STOCKAGE ---
def save_image_to_mongo(image_path):
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    doc = {
        "Id_document": os.path.basename(image_path),
        "documents": image_bytes,     
        "texte_extrait": ""           # vide pour l'instant
    }
    collection.insert_one(doc)
    print(f"[+] Image '{os.path.basename(image_path)}' stockée dans MongoDB ✅")

# --- MAIN ---
def main():
    if not os.path.exists(FOLDER_IMAGES):
        print(f"[!] Le dossier '{FOLDER_IMAGES}' n'existe pas.")
        return

    for file in os.listdir(FOLDER_IMAGES):
        if file.endswith(".jpg"):
            save_image_to_mongo(os.path.join(FOLDER_IMAGES, file))

    print("\n[+] Toutes les images ont été stockées avec succès dans MongoDB.")

if __name__ == "__main__":
    main()
