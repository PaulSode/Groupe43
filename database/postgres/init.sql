-- =============================================================
-- SCHEMA DocFlow — PostgreSQL
-- =============================================================

-- 1. UTILISATEURS
CREATE TABLE utilisateur (
    id_utilisateur SERIAL PRIMARY KEY,
    email          VARCHAR(255) UNIQUE NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    first_name     VARCHAR(100) DEFAULT '',
    last_name      VARCHAR(100) DEFAULT '',
    is_admin       BOOLEAN DEFAULT FALSE,
    date_creation  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. CLIENTS
CREATE TABLE client (
    id_client           SERIAL PRIMARY KEY,
    nom                 VARCHAR(255) NOT NULL,
    prenom              VARCHAR(100) DEFAULT '',
    email               VARCHAR(255),
    telephone           VARCHAR(50) DEFAULT '',
    adresse_facturation TEXT DEFAULT '',
    siret               VARCHAR(14),
    siren               VARCHAR(9),
    tva_intracom        VARCHAR(20) DEFAULT '',
    statut              VARCHAR(20) DEFAULT 'actif'
                        CHECK (statut IN ('actif', 'inactif', 'en_attente')),
    date_creation       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. DOCUMENTS
CREATE TABLE document (
    id_document     SERIAL PRIMARY KEY,
    type_document   VARCHAR(30) NOT NULL,
    id_client       INT NOT NULL REFERENCES client(id_client) ON DELETE CASCADE,
    filename        VARCHAR(255) NOT NULL,
    file_path       TEXT,
    ocr_file_id     VARCHAR(50),
    mongodb_raw_id  VARCHAR(50),
    date_upload     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_emission   VARCHAR(20),
    date_expiration VARCHAR(20),
    statut          VARCHAR(20) DEFAULT 'pending'
                    CHECK (statut IN ('pending', 'processed', 'error', 'manual_review')),
    ocr_confidence  DECIMAL(5,2),
    raw_text        TEXT,
    extracted_data  JSONB
);

-- 4. INCOHÉRENCES
CREATE TABLE incoherence (
    id_incoherence  SERIAL PRIMARY KEY,
    id_document     INT NOT NULL REFERENCES document(id_document) ON DELETE CASCADE,
    type_incoherence VARCHAR(30) NOT NULL,
    severity        VARCHAR(10) DEFAULT 'medium'
                    CHECK (severity IN ('low', 'medium', 'high')),
    message         TEXT NOT NULL,
    field           VARCHAR(50) DEFAULT '',
    expected_value  TEXT,
    actual_value    TEXT,
    resolved        BOOLEAN DEFAULT FALSE,
    date_detection  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. TABLES FILLES (détails par type de document)
CREATE TABLE facture (
    id_document  INT PRIMARY KEY REFERENCES document(id_document) ON DELETE CASCADE,
    total_ht     DECIMAL(12, 2),
    montant_tva  DECIMAL(12, 2),
    total_ttc    DECIMAL(12, 2),
    statut       VARCHAR(50) DEFAULT 'non payé'
);

CREATE TABLE devis (
    id_document    INT PRIMARY KEY REFERENCES document(id_document) ON DELETE CASCADE,
    validite_jours INT,
    total_ht       DECIMAL(12, 2),
    total_ttc      DECIMAL(12, 2),
    est_signe      BOOLEAN DEFAULT FALSE,
    date_signature DATE,
    statut         VARCHAR(50) DEFAULT 'à signer'
);

CREATE TABLE kbis (
    id_document     INT PRIMARY KEY REFERENCES document(id_document) ON DELETE CASCADE,
    greffe          VARCHAR(100),
    numero_gestion  VARCHAR(50),
    forme_juridique VARCHAR(20),
    capital         INT
);

CREATE TABLE avis_sirene (
    id_document         INT PRIMARY KEY REFERENCES document(id_document) ON DELETE CASCADE,
    code_ape            VARCHAR(10),
    activite_principale TEXT,
    date_immatriculation DATE
);

CREATE TABLE attestation_urssaf (
    id_document       INT PRIMARY KEY REFERENCES document(id_document) ON DELETE CASCADE,
    code_securite     VARCHAR(50),
    compte_urssaf     VARCHAR(50),
    date_fin_validite DATE
);

CREATE TABLE rib (
    id_document    INT PRIMARY KEY REFERENCES document(id_document) ON DELETE CASCADE,
    banque         VARCHAR(150),
    code_banque    VARCHAR(10),
    code_guichet   VARCHAR(10),
    numero_compte  VARCHAR(50),
    cle_rib        VARCHAR(5),
    iban           VARCHAR(34),
    bic            VARCHAR(15),
    domiciliation  TEXT
);

-- 6. LIGNES DE TRANSACTION
CREATE TABLE ligne_transaction (
    id_ligne         SERIAL PRIMARY KEY,
    id_document      INT NOT NULL REFERENCES document(id_document) ON DELETE CASCADE,
    designation      TEXT NOT NULL,
    quantite         INT NOT NULL,
    prix_unitaire_ht DECIMAL(12, 2) NOT NULL,
    sous_total_ht    DECIMAL(12, 2) NOT NULL
);

-- 7. INDEX
CREATE INDEX idx_doc_client    ON document(id_client);
CREATE INDEX idx_doc_statut    ON document(statut);
CREATE INDEX idx_doc_type      ON document(type_document);
CREATE INDEX idx_inc_document  ON incoherence(id_document);
CREATE INDEX idx_inc_resolved  ON incoherence(resolved);
CREATE INDEX idx_ligne_doc     ON ligne_transaction(id_document);
