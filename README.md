# MAKOS SACCO Parcel Management System

A Django-based academic project prototype for parcel registration, tracking and branch operations. Requirements are proposed and must be validated with MAKOS SACCO stakeholders before production use.

## Website areas

- **Public website:** Home, About, Services, Branches, Contact and parcel tracking.
- **Staff portal:** Sign in, role-protected dashboard, parcel registration, records and status history.
- **Management portal:** Read-only branch overview for System Administrators and Branch Managers; payment totals are shown only to users with payment-view permission.
- **Access control:** Standard Django Groups provide the System Administrator, Branch Manager, Parcel Clerk, Dispatcher, Driver, Finance Officer and Customer roles. Permissions are synchronized after migrations; staff account management is restricted to System Administrators.

Public pages describe the proposed system and do not claim that planned integrations or operational workflows are already available. The Contact page intentionally does not invent contact details; verified official channels should be added before launch.

## Quick start (Windows PowerShell)

```powershell
cd $HOME\Documents\parcel-management-system
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Create a MySQL database (default configuration expects `makos_parcels`, user `root`, local host and port 3306), then update `.env` with your own database username/password. Never commit `.env` or production credentials.

```powershell
python manage.py makemigrations operations
python manage.py migrate
python manage.py createsuperuser
python manage.py test
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`. Public pages include `/about/`, `/services/`, `/branches/`, `/contact/` and `/track/`. Staff must be assigned a role granting the requested permission. The first superuser can access `/staff/users/` to create accounts and assign roles, and `/management/` for the management overview. To use SQLite for a quick local evaluation only, set `DB_ENGINE=django.db.backends.sqlite3` in `.env`.

## Development branch

Website foundation, role-based access, and staff/management portal work are on `feature/makos-website-foundation`. The `main` branch remains unchanged until review and merge.

## Role permission summary

- **System Administrator:** All operations-app permissions; Django superusers retain Django's built-in permission bypass.
- **Branch Manager:** Broad branch operations, parcel and dispatch management, plus the management overview.
- **Parcel Clerk:** Parcel registration/editing, customer records and tracking events; cannot change parcel status or administer users.
- **Dispatcher:** Dispatch and transport records, parcel status changes and tracking events.
- **Driver:** Read access to assigned-operation data and tracking event creation.
- **Finance Officer:** Payment recording and viewing, with read access to parcel/customer/branch records.
- **Customer:** No staff-operation permissions. Public tracking remains available; customer account workflows are not implemented.

Roles are Django groups, created/synchronized during `migrate` after app permissions exist. Existing accounts must be assigned to an appropriate group by a superuser before they can access staff pages. Role policy is an initial implementation and requires stakeholder/security review before production deployment.

This is an academic MVP, not production-ready. Validate requirements with MAKOS SACCO stakeholders. Configure a strong `SECRET_KEY`, `DEBUG=False`, appropriate `ALLOWED_HOSTS`, secure HTTPS cookies and a production-grade database.
