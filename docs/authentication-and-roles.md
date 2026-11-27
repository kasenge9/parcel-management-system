# Authentication and role-based access control

The project retains Django's built-in session authentication. It does not introduce JWT or browser-stored bearer tokens.

## Roles

| Role | Application access |
| --- | --- |
| Administrator | All Operations model permissions and all role-protected views. Superusers bypass role checks. |
| Clerk | View parcel records and register parcels; customer create/view/change model permissions. |
| Dispatcher | View parcels and update parcel status; dispatch-related model permissions. |
| Management | Dashboard and parcel viewing; read-only Operations model permissions. |

Role checks are enforced server-side in `operations/access.py` and `operations/views.py`. Hiding links in templates is not an access-control mechanism.

## Setup

Run migrations and provision groups:

```powershell
python manage.py migrate
python manage.py shell
```

```python
from operations.role_setup import setup_default_roles
setup_default_roles()
```

Create the initial administrator:

```powershell
python manage.py createsuperuser
```

Assign an existing employee account to a group:

```python
from django.contrib.auth.models import Group, User
user = User.objects.get(username="clerk1")
user.groups.add(Group.objects.get(name="Clerk"))
```

Replace `clerk1` with the real username. Assign only the role required for that employee.

## Access behavior

- Unauthenticated users are redirected to login.
- Successful logins land on the parcel list, which is available to all four staff roles; this avoids sending Clerks and Dispatchers to the restricted dashboard.
- Authenticated users without an allowed role receive HTTP 403.
- Public parcel tracking remains public.
- Dashboard access is Administrator or Management because it displays revenue.
- Parcel registration is Administrator or Clerk.
- Parcel status updates are Administrator or Dispatcher and POST-only.

## Security settings

- Django continues to hash passwords using its configured password hasher.
- Minimum password length is 12 characters, plus Django similarity and common-password validators.
- Sessions use a 30-minute rolling inactivity timeout.
- Session cookies are HttpOnly and SameSite=Lax.
- Secure cookies and HTTPS redirect default to enabled when DEBUG=False.
- Production must set a strong random SECRET_KEY, DEBUG=False, correct ALLOWED_HOSTS, and HTTPS.
- Set CSRF_TRUSTED_ORIGINS for exact HTTPS origins that submit forms.
- HSTS is opt-in. Enable it only after confirming HTTPS works for the domain and required subdomains.

If TLS terminates at a reverse proxy, configure and verify Django's proxy/HTTPS settings to avoid redirect loops. Keep secrets outside source control.

This change does not yet add 2FA, login throttling, password-reset email delivery, or a dedicated authentication audit log; implement and test those separately.
