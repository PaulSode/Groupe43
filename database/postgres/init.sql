-- 1. TABLE UTILISATEUR
CREATE TABLE utilisateur (
    id_utilisateur SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABLE ENTITE
CREATE TABLE entite (
    id_entite SERIAL PRIMARY KEY,
    reference_metier VARCHAR(50) UNIQUE NOT NULL,
    type_entite VARCHAR(3) NOT NULL CHECK (type_entite IN ('B2B', 'B2C')),
    nom VARCHAR(255) NOT NULL,
    prenom VARCHAR(100),
    siren VARCHAR(9),
    siret VARCHAR(14) UNIQUE,
    adresse TEXT NOT NULL,
    email VARCHAR(255),
    telephone VARCHAR(50),
    CONSTRAINT chk_b2c_prenom CHECK (type_entite = 'B2B' OR prenom IS NOT NULL),
    CONSTRAINT chk_b2b_siret CHECK (type_entite = 'B2C' OR siret IS NOT NULL)
);

-- 3. TABLE DOCUMENT (Intégration du pivot MongoDB)
CREATE TABLE document (
    id_document SERIAL PRIMARY KEY,
    numero_document VARCHAR(50) UNIQUE NOT NULL,
    type_document VARCHAR(20) NOT NULL,
    label_classification VARCHAR(50) NOT NULL,
    mongodb_raw_id VARCHAR(24), -- Clé étrangère logique vers MongoDB
    id_emetteur INT NOT NULL REFERENCES entite(id_entite) ON DELETE RESTRICT,
    id_client INT REFERENCES entite(id_entite) ON DELETE RESTRICT,
    date_emission DATE NOT NULL,
    date_integration TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. TABLES FILLES
CREATE TABLE facture (
    id_document INT PRIMARY KEY REFERENCES document(id_document) ON DELETE CASCADE,
    total_ht DECIMAL(12, 2) NOT NULL,
    montant_tva DECIMAL(12, 2) NOT NULL,
    total_ttc DECIMAL(12, 2) NOT NULL,
    statut VARCHAR(50) DEFAULT 'non payé'
);

CREATE TABLE devis (
    id_document INT PRIMARY KEY REFERENCES document(id_document) ON DELETE CASCADE,
    validite_jours INT NOT NULL,
    total_ht DECIMAL(12, 2) NOT NULL,
    total_ttc DECIMAL(12, 2) NOT NULL,
    est_signe BOOLEAN DEFAULT FALSE,
    date_signature DATE,
    statut VARCHAR(50) DEFAULT 'à signer',
    CONSTRAINT chk_signature CHECK (est_signe = FALSE OR date_signature IS NOT NULL)
);

CREATE TABLE kbis (
    id_document INT PRIMARY KEY REFERENCES document(id_document) ON DELETE CASCADE,
    greffe VARCHAR(100) NOT NULL,
    numero_gestion VARCHAR(50) NOT NULL,
    forme_juridique VARCHAR(20) NOT NULL,
    capital INT NOT NULL
);

CREATE TABLE avis_sirene (
    id_document INT PRIMARY KEY REFERENCES document(id_document) ON DELETE CASCADE,
    code_ape VARCHAR(10) NOT NULL,
    activite_principale TEXT NOT NULL,
    date_immatriculation DATE NOT NULL
);

CREATE TABLE attestation_urssaf (
    id_document INT PRIMARY KEY REFERENCES document(id_document) ON DELETE CASCADE,
    code_securite VARCHAR(50) UNIQUE NOT NULL,
    compte_urssaf VARCHAR(50) NOT NULL,
    date_fin_validite DATE NOT NULL
);

CREATE TABLE rib (
    id_document INT PRIMARY KEY REFERENCES document(id_document) ON DELETE CASCADE,
    banque VARCHAR(150) NOT NULL,
    code_banque VARCHAR(10) NOT NULL,
    code_guichet VARCHAR(10) NOT NULL,
    numero_compte VARCHAR(50) NOT NULL,
    cle_rib VARCHAR(5) NOT NULL,
    iban VARCHAR(34) UNIQUE NOT NULL,
    bic VARCHAR(15) NOT NULL,
    domiciliation TEXT NOT NULL
);

-- 5. TABLE TRANSACTION
CREATE TABLE ligne_transaction (
    id_ligne SERIAL PRIMARY KEY,
    id_document INT NOT NULL REFERENCES document(id_document) ON DELETE CASCADE,
    designation TEXT NOT NULL,
    quantite INT NOT NULL,
    prix_unitaire_ht DECIMAL(12, 2) NOT NULL,
    sous_total_ht DECIMAL(12, 2) NOT NULL
);

-- 6. INDEX DE PERFORMANCE
CREATE INDEX idx_doc_emetteur ON document(id_emetteur);
CREATE INDEX idx_doc_client ON document(id_client);
CREATE INDEX idx_ligne_doc ON ligne_transaction(id_document);
CREATE INDEX idx_doc_mongo_id ON document(mongodb_raw_id);