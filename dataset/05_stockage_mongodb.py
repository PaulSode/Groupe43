import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
FOLDER_IMAGES = "dataset_images_final"  # dossier des images déjà bruitées

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_PORT")
DB_NAME = os.getenv("MONGO_DB")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION")

MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"

# --- MONGODB SETUP ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --- FONCTION DE STOCKAGE ---
def save_image_to_mongo(image_path):
    
    last_doc = collection.find_one(sort=[("id_document", -1)]) 
    next_id = 1 if last_doc is None else last_doc["id_document"] + 1

    date_integration = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    doc = {
        "id_document": next_id
        "date_integration": date_integration
        "nom_document": os.path.basename(image_path),
        "document": image_bytes,     
        "texte_extrait_OCR": ""           # vide pour l'instant
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
