# MAKOS SACCO Parcel Management System

A Django-based academic project prototype for parcel registration, tracking and branch operations. The requirements are proposed and must be validated with MAKOS SACCO stakeholders before production use.

## Quick start (Windows PowerShell)

```powershell
cd $HOME\Documents\parcel-management-system
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Create a MySQL database (default configuration expects `makos_parcels`, user `root`, local host and port 3306), then update `.env` with your own database username/password. Never commit `.env` or real credentials.

```powershell
python manage.py makemigrations operations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`. Public tracking is at `/track/`; staff operations require login. To use SQLite for a quick local evaluation only, set `DB_ENGINE=django.db.backends.sqlite3` and `DB_NAME=db.sqlite3` in `.env`.

## First setup after cloning

The repository was initially empty, so after pulling these files run the commands above. If you have not yet connected your local clone to GitHub credentials, GitHub's HTTPS prompt or Git Credential Manager will guide authentication. Do not paste passwords or access tokens into chat or commit them to the repository.

## Initial functionality

- Responsive MAKOS-branded landing page and public parcel tracking lookup.
- Authenticated staff dashboard and parcel register.
- Register parcels with sender, recipient, route, weight, description and fee.
- Unique tracking codes and append-only tracking events for status changes.
- Branch, customer, payment, vehicle, driver and dispatch data models available through Django admin.
- Revenue and parcel status summary cards.

This is an academic MVP, not production-ready. Before real use, add and test role-based authorization, payment reconciliation, dispatch workflows, audit controls, PDF receipts/reports, notifications, privacy and security review, backups, HTTPS, and deployment settings. Configure a strong `SECRET_KEY`, `DEBUG=False`, and appropriate `ALLOWED_HOSTS` before deployment.
