# MAKOS SACCO Parcel Management System

A Django-based academic project prototype for parcel registration, tracking and branch operations. The requirements are proposed and must be validated with MAKOS SACCO stakeholders before production use.

## Website areas

- **Public website:** Home, About, Services and parcel tracking.
- **Staff portal:** Sign in, parcel dashboard, parcel registration, parcel records and status history.
- **Management foundation:** Django admin and existing operational data models. Role-specific permissions and advanced management workflows are planned enhancements.

The public About and Services pages describe the proposed system. They do not claim that planned integrations or workflows are already operational.

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
python manage.py test
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`. Public pages include `/about/`, `/services/` and `/track/`; staff operations require login. To use SQLite for a quick local evaluation only, set `DB_ENGINE=django.db.backends.sqlite3` and `DB_NAME=db.sqlite3` in `.env`.

## Development branch

Website foundation work is being developed on `feature/makos-website-foundation`. The `main` branch is kept unchanged until the work is reviewed and merged.

## Current prototype functionality

- Responsive MAKOS-branded layout with shared navigation and footer.
- Public home, About, Services and parcel tracking pages.
- Authenticated staff dashboard and parcel register.
- Register parcels with sender, recipient, route, weight, description and fee.
- Unique tracking codes and tracking events for status changes.
- Branch, customer, payment, vehicle, driver and dispatch data models available through Django admin.
- Revenue and parcel status summary cards.
- Initial automated tests for public website routes.

## Planned enhancements

Role-based authorization, customer accounts, branch transfer and dispatch workflows, payment reconciliation and M-Pesa integration, PDF receipts/reports, SMS/email notifications, QR scanning, collection verification, audit controls, analytics, backups and deployment hardening.

This is an academic MVP, not production-ready. Requirements must be validated with MAKOS SACCO stakeholders before real use. Configure a strong `SECRET_KEY`, `DEBUG=False`, appropriate `ALLOWED_HOSTS`, HTTPS and secure backups before deployment.