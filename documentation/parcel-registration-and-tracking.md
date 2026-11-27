# Parcel registration and tracking workflow

This guide describes the parcel workflow currently implemented in the Django prototype. Operational rules, labels, and staff responsibilities should be confirmed with MAKOS SACCO before production use.

## Registering a parcel

A user with the Parcel Clerk, Branch Manager, or System Administrator permissions can open the staff parcel registration form. The form collects:

- sender name and phone number;
- recipient name and phone number;
- parcel description and weight;
- active origin and destination branches;
- delivery fee in Kenyan shillings.

The form rejects blank descriptions, non-positive weights, and negative delivery fees. Inactive branches are excluded from the origin and destination choices. On save, the system reuses the first existing customer record with the submitted phone number, or creates a customer record if no match exists. Existing customer names are not silently overwritten when a phone number is reused.

Parcel creation and the initial tracking event are wrapped in one database transaction. A failed registration therefore does not leave a parcel without its first event. The generated tracking code is shown after successful registration.

## Staff parcel register

Staff can search the parcel register using a tracking code, sender name or phone, or recipient name or phone. They can filter by the current parcel status. Results are paginated at 25 parcels per page and ordered newest first.

## Tracking updates

System Administrators, Branch Managers and Dispatchers can update parcel status. The update endpoint accepts POST requests only. Each successful status change is saved together with a tracking event in one transaction, including:

- the new status;
- the optional operational location;
- an optional staff-only note;
- the authenticated staff account and timestamp.

The parcel row is locked during the update to reduce the risk of two staff members overwriting one another's changes. Submitting the current status again does not create a duplicate event. Invalid status values are rejected.

This version deliberately does not enforce a fixed status-transition state machine. The approved operational sequence (including returns, cancellations, payment holds and collection) must be agreed with SACCO operations before such restrictions are introduced.

## Public tracking privacy

Customers can enter a tracking code without signing in. Codes are normalized to uppercase. The public page shows the parcel tracking code, route, current status and event dates/locations in chronological order.

Sender and recipient phone numbers, names and internal staff notes are not shown on the public tracking page. Staff with parcel-view permission can view contact details and internal notes in the protected parcel detail page.

A tracking code is a lookup reference, not proof of identity. Collection authorization, one-time collection PINs and customer account access are future features and must not be inferred from public tracking.

## Permissions

- Parcel Clerk: register and view parcels; cannot update parcel status.
- Dispatcher: view parcels and record status/tracking updates.
- Branch Manager and System Administrator: view parcels and record status/tracking updates.

The parcel detail page only renders the status-update form for those authorized roles. Server-side role checks remain authoritative even if a user manually submits a request.

## Tests

Automated tests cover parcel registration, customer reuse by phone, active-branch validation, positive weight and non-negative fee checks, initial tracking event creation, role restrictions, tracking update metadata, POST-only updates, invalid status rejection, chronological history, staff-only notes, public contact privacy, parcel search and status filtering.
