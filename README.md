# Blockchain-Based Tendering (Django)

## Overview

This repository contains a Django-based tendering application that integrates a simple blockchain module to record tender/bid events. It provides:
- User registration, authentication and profile management (including MFA fields)
- Tender CRUD (create, list, detail, delete)
- Bidding and awarding workflows
- A lightweight blockchain implementation and visualizer to inspect recorded blocks
- Templates and static assets for a small web UI

## Stack

- Python (3.x)
- Django (see `requirements.txt`)
- SQLite (default development DB: `db.sqlite3`)
- HTML/CSS templates (Django templating)
- Simple, local blockchain module (`blockchain/Block.py`, `blockchain/Chain.py`, `blockchain/GlobalChain.py`)

## Key files and folders

- `manage.py` — Django management entrypoint
- `blockchain_based_tender/` — Django project settings and ASGI/WGI
- `blockchain/` — simple blockchain implementation and JSON data files (`blockchain_data.json`, `tender_blockchain.json`)
- `tenders/` — app handling tender models, views, templates, and blockchain integration
- `users/` — app handling user models, MFA and authentication
- `templates/` and `static/` — UI templates and CSS
- `requirements.txt` — Python dependencies
- `db.sqlite3` — development database (SQLite)

## Setup (Windows)

1. Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Apply migrations and create a superuser:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

4. Run the development server:

```powershell
python manage.py runserver
```

Open http://127.0.0.1:8000/ in a browser.

## Running tests

```powershell
python manage.py test
```

## Configuration & Notes

- For production use replace SQLite with a production-grade database and set a secure `SECRET_KEY` and appropriate `DEBUG` and `ALLOWED_HOSTS` in `blockchain_based_tender/settings.py` or via environment variables.
- Blockchain data used for visualizations is stored in `blockchain/blockchain_data.json` and `tender_blockchain.json` — these are sample/local stores for the demo blockchain.
- To reset the local DB (development only): stop the server, remove `db.sqlite3`, then run `python manage.py migrate` again.

## Where to look for features

- Tender views & templates: `tenders/views.py` and `templates/tenders/`
- Blockchain logic: `blockchain/Block.py`, `blockchain/Chain.py`, `blockchain/GlobalChain.py` and JSON files
- User and MFA logic: `users/models.py`, `users/forms.py`, `templates/users/`

