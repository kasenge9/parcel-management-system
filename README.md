# MAKOS SACCO Parcel Management System

A Django-based academic project prototype for parcel registration, tracking and branch operations. The requirements are proposed and must be validated with MAKOS SACCO stakeholders before production use.

## Website areas

- **Public website:** Home, About, Services and parcel tracking.
- **Staff portal:** Sign in, role-protected parcel dashboard, registration, records and status history.
- **Access control:** Standard Django Groups provide the System Administrator, Branch Manager, Parcel Clerk, Dispatcher, Driver, Finance Officer and Customer roles. Permissions are synchronized after migrations; staff account management is restricted to System Administrators.
- **Management foundation:** Django admin and existing operational data models. Advanced management workflows remain planned enhancements.

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

Create a MySQL database (default configuration expects `makos_parcels`, user `root`, local host and port 3306), then update `.env` with your own database username/password. Never commit `.env` or production credentials.

```powershell
python manage.py makemigrations operations
python manage.py migrate
python manage.py createsuperuser
python manage.py test
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`. Public pages include `/about/`, `/services/` and `/track/`; staff pages require a role granting the relevant permission. The first superuser can access `/staff/users/` to create accounts and assign roles. To use SQLite for a quick local evaluation only, set `DB_ENGINE=django.db.backends.sqlite3` in `.env`.

## Development branch

Website foundation and RBAC work are being developed on `feature/makos-website-foundation`. The `main` branch is kept unchanged until the work is reviewed and merged.

## Current prototype functionality

- Responsive MAKOS-branded layout with shared navigation and footer.
- Public home, About, Services and parcel tracking pages.
- Role-based authorization using Django permissions and groups.
- Administrator-only user creation and role assignment.
- Authenticated, permission-protected staff dashboard and parcel workflows.
- Register parcels with sender, recipient, route, weight, description and fee.
- Unique tracking codes and tracking events for status changes.
- Branch, customer, payment, vehicle, driver and dispatch data models available through Django admin.
- Revenue summary shown only to users with payment-view permission.
- Automated tests for public routes and RBAC access rules.

## Role permission summary

- **System Administrator:** All operations-app permissions; Django superusers retain Django's built-in permission bypass.
- **Branch Manager:** Broad branch operations, including parcel and dispatch management.
- **Parcel Clerk:** Parcel registration and editing, customer records, tracking events and payment visibility.
- **Dispatcher:** Dispatch and transport records, parcel updates and tracking events.
- **Driver:** Read access to assigned-operation data and tracking event creation.
- **Finance Officer:** Payment recording and viewing, with read access to parcel/customer/branch records.
- **Customer:** No staff-operation permissions. Public tracking remains available; customer account workflows are not implemented.

Roles are Django groups, created/synchronized during `migrate` after app permissions exist. Existing accounts must be assigned to an appropriate group by a superuser before they can access staff pages. Role policy is a starting point and needs stakeholder/security review before production deployment.

This is an academic MVP, not production-ready. Requirements must be validated with MAKOS SACCO stakeholders before real use. Configure a strong `SECRET_KEY`, `DEBUG=False`, appropriate `ALLOWED_HOSTS`, secure HTTPS cookies and a production-grade database.
