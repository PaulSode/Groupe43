db = db.getSiblingDB("hackathon");

// RAW documents
db.createCollection("documents_raw");

// OCR text
db.createCollection("documents_ocr");

// extracted fields
db.createCollection("documents_extracted");

// logs
db.createCollection("processing_logs");

db.createCollection("ground_truth");
