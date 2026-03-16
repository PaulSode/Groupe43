import os
import cv2
import fitz  # PyMuPDF
import numpy as np
import random

# --- CONFIGURATION ---
FOLDERS_TO_PROCESS = ["factures_pdf", "devis_pdf", "admin_pdf"]
OUTPUT_IMAGE_FOLDER = "dataset_images_final"
PROBABILITE_BRUIT = 0.7 

def add_stains(img):
    h, w = img.shape[:2]
    num_stains = random.randint(1, 4)
    for _ in range(num_stains):
        center = (random.randint(0, w), random.randint(0, h))
        axes = (random.randint(20, 100), random.randint(10, 50))
        angle = random.randint(0, 360)
        overlay = img.copy()
        color = (random.randint(150, 220), random.randint(180, 230), random.randint(200, 240))
        cv2.ellipse(overlay, center, axes, angle, 0, 360, color, -1)
        alpha = random.uniform(0.2, 0.5)
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
    return img

def apply_degradations(img):
    h, w = img.shape[:2]
    # Rotation
    angle = random.uniform(-2, 2)
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1)
    img = cv2.warpAffine(img, M, (w, h), borderValue=(255, 255, 255))
    # Taches
    if random.random() < 0.6:
        img = add_stains(img)
    # Flou
    if random.random() < 0.4:
        k = random.choice([3, 5])
        img = cv2.GaussianBlur(img, (k, k), 0)
    # Bruit gaussien
    noise = np.random.normal(0, random.randint(5, 12), img.shape).astype(np.uint8)
    img = cv2.add(img, noise)
    # Luminosité
    img = cv2.convertScaleAbs(img, alpha=random.uniform(0.8, 1.1), beta=random.randint(-15, 10))
    return img

def traiter_dataset():
    os.makedirs(OUTPUT_IMAGE_FOLDER, exist_ok=True)
    
    for folder in FOLDERS_TO_PROCESS:
        if not os.path.exists(folder): continue
            
        print(f"Traitement : {folder}")
        for file in os.listdir(folder):
            if file.endswith(".pdf"):
                path_pdf = os.path.join(folder, file)
                
                # Ouverture via PyMuPDF (Zéro Poppler)
                doc = fitz.open(path_pdf)
                
                for i, page in enumerate(doc):
                    # Rendu de la page en 300 DPI
                    pix = page.get_pixmap(dpi=300)
                    
                    # Conversion directe Pixmap -> Numpy (BGR pour OpenCV)
                    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR) if pix.n == 3 else cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                    
                    if random.random() < PROBABILITE_BRUIT:
                        img = apply_degradations(img)
                        label = "noisy"
                    else:
                        label = "clean"
                    
                    output_name = f"{os.path.splitext(file)[0]}_p{i}_{label}.jpg"
                    cv2.imwrite(os.path.join(OUTPUT_IMAGE_FOLDER, output_name), img, [int(cv2.IMWRITE_JPEG_QUALITY), random.randint(50, 90)])
                doc.close()
                print("Dégradation visuelle terminée")

if __name__ == "__main__":
    traiter_dataset()