# Initial project requirements

## Objective
Design and implement a browser-accessible parcel registration, movement and tracking system for MAKOS SACCO. This is a proposed academic scope and is not a verified description of the SACCO's actual processes; requirements should be validated through stakeholder interviews, observation or questionnaires.

## Stakeholders
- Administrator: staff access and reference data management.
- Clerk: parcel registration and customer updates.
- Dispatcher/driver: transport and arrival updates.
- Customer: tracking lookup using a parcel code.
- Management: operational and financial summaries.

## Functional requirements (initial)
1. Staff authenticate before accessing operations pages.
2. Staff register sender, recipient, parcel details, branches and delivery fee.
3. System assigns each parcel a unique tracking code.
4. Status changes preserve dated tracking events.
5. Public tracking lookup does not expose customer contact details.
6. Staff can view/search parcel records and dashboard summaries.
7. Database domain includes payments and transport entities for later workflow increments.

## Non-functional requirements
- Responsive interface for desktop and mobile browsers.
- CSRF protection and authenticated staff operations.
- MySQL relational database configuration; SQLite may be used for local evaluation.
- Keep historical parcel events rather than overwriting them.

## Deferred scope
Role-specific permissions, payment recording/reconciliation, dispatch assignment, PDF receipts/reports, notifications, automated tests, audit logging, deployment hardening and user acceptance testing. Verify rules with MAKOS SACCO before production use.
