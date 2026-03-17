FROM python:3.12-slim

WORKDIR /app

# Ajout de build-essential (gcc, make) et python3-dev
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "python 01_extraction_entites_api.py && python 02_generation_dataset_complet.py && python 03_generateur_pdf_unifie.py && python 04_degradation_visuelle.py"]