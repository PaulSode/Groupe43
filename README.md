# Groupe 43

# DocFlow — Plateforme de traitement documentaire automatisé

## Sommaire

- [Architecture générale](#architecture-générale)
- [Prérequis](#prérequis)
- [Installation et démarrage](#installation-et-démarrage)
- [Services](#services)
- [Base de données](#base-de-données)
- [Pipeline de traitement documentaire](#pipeline-de-traitement-documentaire)
- [API REST](#api-rest)
- [Frontend](#frontend)
- [Génération du jeu de données](#génération-du-jeu-de-données)
- [Variables d'environnement](#variables-denvironnement)

---

## Architecture générale

Le projet repose sur une architecture microservices orchestrée par Docker Compose, composée de :

- Un **backend FastAPI** (Python) exposant une API REST
- Un **frontend React** (TypeScript) constituant l'interface utilisateur
- Une base de données **PostgreSQL** pour les données structurées
- une base de données **MongoDB** pour le stockage des images brutes et des données OCR
- Un service de **génération de données synthétiques** (mode préparation uniquement)

```
frontend (React)  <-->  services/api (FastAPI)  <-->  PostgreSQL
                                                  <-->  MongoDB
```

---

## Prérequis

- Docker >= 24
- Docker Compose >= 2.20
- Node.js >= 16
- Python >= 3.12

---

## Installation et démarrage

### 1. Configurer l'environnement

```bash
cp .env.example .env
```

Modifier les valeurs dans `.env` si nécessaire (voir la section Variables d'environnement).

### 2. Démarrer les services principaux

```bash
docker compose up --build
```

Les services suivants démarrent :

- PostgreSQL sur le port `5432`
- MongoDB sur le port `27017`
- API FastAPI sur le port `8000`

### 3. Générer le jeu de données (optionnel)

Le profil `data_prep` lance le service de génération de données synthétiques :

```bash
docker compose --profile data_prep up generateur_donnees
```

Ce service enchaîne automatiquement les scripts d'extraction, de génération, de rendu PDF et de bruitage visuel.

### 4. Démarrer le frontend

```bash
cd frontend
cp .env.example .env
npm install
npm start
```

L'application est accessible sur `http://localhost:3000`.

---

## Services

### API (`services/`)

Le backend est développé avec **FastAPI** et organisé en modules fonctionnels :

| Module | Responsabilité |
|---|---|
| `auth/` | Authentification JWT (inscription, connexion, vérification) |
| `clients/` | CRUD des clients, recherche, mise à jour |
| `documents/` | Upload, classification, extraction OCR, gestion du cycle de vie |
| `incoherences/` | Détection et résolution des anomalies documentaires |
| `dashboard/` | Calcul des statistiques globales |
| `ocr/` | Extraction de texte via EasyOCR (images et PDF via PyMuPDF) |
| `classifier/` | Classification automatique du type de document par regex |
| `extractor/` | Extraction des champs structurés (SIRET, IBAN, montants, dates...) |
| `validator/` | Vérification de cohérence inter-documents |
| `datalake/` | Persistance dans MongoDB (zone raw et zone curated) |

### Frontend (`frontend/`)

Interface React TypeScript organisée en pages, composants réutilisables, contextes et couche API centralisée.

---

## Base de données

### PostgreSQL

Le schéma est initialisé automatiquement au premier démarrage via `database/postgres/init.sql`.

Tables principales :

- `utilisateur` : comptes utilisateurs
- `client` : fiche client avec données légales (SIRET, SIREN, TVA)
- `document` : métadonnées et données extraites de chaque document
- `incoherence` : anomalies détectées sur les documents
- `facture`, `devis`, `kbis`, `rib`, `avis_sirene`, `attestation_urssaf` : tables filles par type de document
- `ligne_transaction` : lignes de détail des factures et devis

### MongoDB

Deux collections principales sont utilisées :

- `images_raw` (GridFS) : stockage binaire des fichiers originaux
- `ocr_curated` : données structurées issues de l'extraction OCR

---

## Pipeline de traitement documentaire

Lorsqu'un document est uploadé via l'API :

1. Le fichier est sauvegardé sur le disque local (`/uploads`)
2. Le texte est extrait via **EasyOCR** (avec conversion PDF -> PNG si nécessaire via PyMuPDF)
3. Le type de document est déterminé par le **classifier** (correspondance par expressions régulières)
4. Les champs structurés sont extraits par l'**extractor** (SIRET, SIREN, TVA, montants, IBAN, dates...)
5. Les données brutes et structurées sont sauvegardées dans **MongoDB**
6. Les métadonnées sont enregistrées dans **PostgreSQL**
7. Les **incohérences** sont générées automatiquement (désaccord avec la fiche client, SIRET invalide Luhn, date expirée, conflit inter-documents)
8. Le **statut final** est calculé : `processed`, `manual_review` ou `error`

Un document passe en `manual_review` si le score de confiance OCR est inférieur à 70%, si des champs obligatoires sont manquants, ou si des incohérences non résolues subsistent.

---

## API REST

L'API est accessible sur `http://localhost:8000`. La documentation interactive (Swagger) est disponible à `/docs`.

### Authentification

| Methode | Route | Description |
|---|---|---|
| POST | `/api/auth/register` | Créer un compte |
| POST | `/api/auth/login` | Se connecter (retourne un JWT) |
| GET | `/api/auth/verify` | Vérifier un token |

### Clients

| Methode | Route | Description |
|---|---|---|
| GET | `/api/clients` | Lister tous les clients |
| GET | `/api/clients/search?q=` | Rechercher des clients |
| POST | `/api/clients` | Créer un client |
| PUT | `/api/clients/{id}` | Modifier un client |
| DELETE | `/api/clients/{id}` | Supprimer un client |

### Documents

| Methode | Route | Description |
|---|---|---|
| GET | `/api/documents` | Lister tous les documents |
| GET | `/api/documents/manual-review` | Documents en attente de traitement manuel |
| POST | `/api/documents/upload` | Uploader un ou plusieurs fichiers |
| GET | `/api/documents/{id}/file` | Récupérer le fichier source |
| PATCH | `/api/documents/{id}/status` | Mettre à jour le statut et les données extraites |
| POST | `/api/documents/{id}/reprocess` | Relancer le traitement OCR |
| DELETE | `/api/documents/{id}` | Supprimer un document |

### Incohérences

| Methode | Route | Description |
|---|---|---|
| GET | `/api/incoherences` | Toutes les incohérences non résolues |
| GET | `/api/documents/{id}/incoherences` | Incohérences d'un document |
| POST | `/api/incoherences/{id}/resolve` | Marquer une incohérence comme résolue |

### Dashboard

| Methode | Route | Description |
|---|---|---|
| GET | `/api/dashboard/stats` | Statistiques globales |

---

## Frontend

### Pages

**Tableau de bord** (`/dashboard`)
Vue d'ensemble avec six indicateurs clés (documents totaux, en attente, traités, en erreur, clients, incohérences actives) et un graphe de performance OCR. Accès rapide aux actions fréquentes.

**Import** (`/upload`)
Zone de glisser-déposer pour uploader des fichiers PDF ou image. Nécessite la sélection préalable d'un client via un champ de recherche autocomplété. Affichage de la progression en temps réel pour chaque fichier.

**Clients** (`/clients`)
Liste paginable et filtrable des clients. Permet la création, la modification et la suppression de fiches clients. Un panneau dédié liste les documents associés à chaque client.

**Documents** (`/documents`)
Grille de tous les documents avec filtres combinés par type et par statut. Chaque carte affiche un aperçu miniature du fichier, le score de confiance OCR et les éventuelles incohérences. Permet la visualisation détaillée, le retraitement et la suppression.

**Visionneuse de document**
Composant modal affichant le fichier source côte à côte avec les données extraites. Les champs manquants sont signalés, les incohérences listées avec possibilité de correction automatique depuis la valeur de la fiche client.

**Traitement manuel** (`/traitement-manuel`)
Interface dédiée aux documents en attente d'intervention humaine. Une file d'attente à gauche, un formulaire de correction à droite n'affichant que les champs vides ou incohérents. La validation déclenche un recalcul du statut côté serveur.

### Technologies utilisées

- React 18 avec TypeScript
- React Router v6 pour la navigation
- Axios pour les appels API
- CSS custom avec variables globales (sans framework UI externe)
- Authentification par JWT stocké en localStorage

---

## Génération du jeu de données

Les scripts de génération se trouvent dans `dataset/` et `tests/`. Ils permettent de créer un jeu de données synthétique complet :

| Script | Description |
|---|---|
| `01_extraction_entites_api.py` | Extraction d'entités réelles depuis l'API Recherche Entreprises du gouvernement |
| `02_generation_dataset_complet.py` | Génération de factures, devis et documents administratifs avec anomalies intentionnelles |
| `03_generateur_pdf_unifie.py` | Rendu des données en fichiers PDF via Jinja2 et xhtml2pdf |
| `04_degradation_visuelle.py` | Bruitage visuel des PDFs (rotation, taches, flou, bruit gaussien) via OpenCV |
| `05_stockage_mongodb.py` | Ingestion des images générées dans MongoDB |

Le taux d'anomalies est configurable via la constante `PROBA_INCOHERENCE` dans le script 02 (défaut : 30%).

---

## Variables d'environnement

Copier `.env.example` en `.env` et ajuster les valeurs :

```env
# PostgreSQL
POSTGRES_USER=admin
POSTGRES_PASS=admin123
POSTGRES_DB=hackathon
POSTGRES_HOST=postgresdb
POSTGRES_PORT=5432

# MongoDB
MONGO_USER=admin
MONGO_PASS=admin123
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB=Data_Mongodb

# JWT
JWT_SECRET=hackathon-groupe43-secret-key
```

La variable `JWT_SECRET` doit être changée pour tout déploiement en dehors d'un environnement de développement local.

---

## Structure du dépôt

```
.
├── database/
│   ├── mongo/          # Script d'initialisation MongoDB
│   └── postgres/       # Schema SQL PostgreSQL
├── dataset/            # Scripts de génération du jeu de données
├── frontend/           # Application React TypeScript
│   └── src/
│       ├── api/        # Couche d'appels API (Axios)
│       ├── components/ # Composants réutilisables
│       ├── contexts/   # Contextes React (authentification)
│       ├── pages/      # Pages de l'application
│       ├── styles/     # CSS global
│       └── types/      # Types TypeScript partagés
├── services/           # Backend FastAPI
│   ├── api/            # Configuration principale, modèles, dépendances
│   ├── auth/           # Service d'authentification
│   ├── classifier/     # Classification automatique des documents
│   ├── clients/        # Gestion des clients
│   ├── dashboard/      # Statistiques
│   ├── datalake/       # Client MongoDB
│   ├── documents/      # Traitement et gestion des documents
│   ├── extractor/      # Extraction des champs structurés
│   ├── incoherences/   # Détection des anomalies
│   ├── ocr/            # Service OCR (EasyOCR + PyMuPDF)
│   └── validator/      # Validation inter-documents
├── tests/              # Scripts de test de génération
├── docker-compose.yml
└── .env.example
```
