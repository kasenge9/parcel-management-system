# Parcel registration and tracking workflow

## Registration
Parcel Clerks and users with parcel-add permission can register a parcel. The form captures sender and recipient details, parcel description, weight, origin, destination, and delivery fee. The model generates a unique tracking code. The parcel and its initial registration event are saved in one transaction.

## Tracking updates
System Administrators, Branch Managers, and Dispatchers can submit status updates using POST. Each event records a valid status, current location, optional customer-facing note, timestamp, and staff account. The parcel status and event are saved atomically. Repeating the current status does not create a duplicate event.

## Public tracking and privacy
Visitors can search by tracking code and see the current status, route, event locations, notes, and timestamps. Sender and recipient names, phone numbers, payment information, and staff usernames are not displayed publicly.

## Before production
Confirm the status lifecycle with MAKOS SACCO. Normalize Kenyan phone formats before importing customer records. Treat tracking codes as private lookup tokens and add rate limiting and monitoring before public launch. Notifications, collection PINs, M-Pesa, barcode scanning, and proof of delivery are not included in this phase.
