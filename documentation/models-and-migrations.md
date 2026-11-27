# Operations models and migration policy

This document describes the data rules implemented by the Django models in `operations/models.py`. It is an implementation guide, not a statement that MAKOS SACCO has approved every business rule. Confirm operational policies with SACCO stakeholders before production use.

## Required values and nullability

Django fields are non-nullable by default. A field is optional only when its model definition explicitly uses `blank=True`, `null=True`, or both as appropriate.

- Branch name and location are required; branch phone is optional.
- Customer full name and phone are required; email is optional.
- Parcel sender, recipient, description, weight, origin, destination and delivery fee are required. Status and timestamps have defaults.
- Payment parcel, amount and method are required. Reference is optional; `received_by` is nullable so a staff account can be removed without erasing the payment.
- Dispatch vehicle, driver, origin and destination are required. Arrival time is nullable until the trip is marked as arrived.
- Tracking event parcel and status are required. Location and note are optional. `created_by` is nullable to preserve the event if a user account is deleted.

Whitespace-only values are rejected by the relevant model `clean()` methods. Standard Django forms and ModelForms run model validation. Code that creates or updates model instances directly should call `full_clean()` before `save()`; Django does not call `full_clean()` automatically.

## Tracking number

Parcel tracking numbers are generated when a parcel is saved without a number. The current format is `MK` followed by ten uppercase letters or digits. The database unique constraint prevents duplicate codes, and the field is indexed for lookup. The generated code is a reference identifier, not an authentication secret.

## Numeric and time constraints

The database enforces the following invariants, including for writes that bypass Django forms:

| Model | Rule | Database constraint |
| --- | --- | --- |
| Parcel | Weight must be greater than zero | `parcel_weight_gt_zero` |
| Parcel | Delivery fee must be zero or greater | `parcel_delivery_fee_nonnegative` |
| Payment | Payment amount must be greater than zero | `payment_amount_gt_zero` |
| Dispatch | Arrival must be null or at/after departure | `dispatch_arrival_after_departure` |

The model `clean()` methods provide readable validation errors for forms and application code. Database constraints are the final integrity boundary.

## Foreign-key deletion policy

| Relationship | Policy | Reason |
| --- | --- | --- |
| Parcel to sender/recipient customers | `PROTECT` | A customer referenced by a parcel cannot be deleted accidentally. |
| Parcel to origin/destination branches | `PROTECT` | Preserve branch references in parcel history. |
| Tracking event to parcel | `CASCADE` | An event has no meaning without its parcel. |
| Tracking event to creating user | `SET_NULL` | Preserve event history if the user is removed. |
| Payment to parcel | `PROTECT` | Preserve financial records and their parcel reference. |
| Payment to receiving user | `SET_NULL` | Preserve the payment if the staff account is removed. |
| Dispatch to vehicle, driver and branches | `PROTECT` | Preserve historical transport references. |
| Dispatch item to dispatch | `CASCADE` | Dispatch line items cannot exist without their dispatch. |
| Dispatch item to parcel | `PROTECT` | A parcel on a dispatch cannot be deleted accidentally. |

## Migration workflow

1. Update the model definitions on a feature branch.
2. Run `python manage.py makemigrations operations`.
3. Review the generated migration; never rewrite a migration that has already been applied to a shared database.
4. Run `python manage.py makemigrations --check --dry-run` and `python manage.py migrate` against a disposable local database.
5. Run `python manage.py test` and review the migration SQL where database behavior is important.
6. Submit the model code, migration, tests and documentation together in a pull request.

The initial schema is `0001_initial.py`; the validation constraints are introduced in `0002_domain_constraints.py`.

### Existing database preflight

Adding a check constraint can fail if existing rows violate it. Before applying `0002_domain_constraints` to a database that already contains operational data, inspect:

- parcels with `weight_kg <= 0`;
- parcels with `delivery_fee < 0`;
- payments with `amount <= 0`;
- dispatches where `arrived_at < departure_time`.

Resolve any rows through an approved correction process and retain an audit trail. Back up the database before production migrations. The migration intentionally does not guess how to correct financial or operational records.

## CI expectations

The GitHub Actions workflow uses SQLite for repeatable automated validation. It installs dependencies, runs Django system checks, verifies that model changes have committed migrations, applies migrations to a fresh database and runs the full test suite. Production database compatibility still needs to be tested separately against the selected MySQL version.
