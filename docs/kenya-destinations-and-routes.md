# MAKOS SACCO destinations and routes

This application is an internal parcel operations system for **MAKOS SACCO only**. It is not a marketplace or a directory of third-party transport companies.

## Operating model

MAKOS SACCO is responsible for the complete parcel workflow:

1. Register senders, recipients and parcels.
2. Maintain MAKOS branches and Kenya-wide destinations.
3. Assign MAKOS routes.
4. Manage vehicles, drivers and dispatches.
5. Receive parcels at MAKOS locations and coordinate delivery or collection.
6. Maintain payments, tracking events and customer updates.

No external courier, passenger coach company or freight operator is part of the operating workflow. The route list is configured under MAKOS SACCO, and old third-party operator, route and service-point records are removed by the seed command. Existing parcel records and tracking numbers are preserved; any legacy third-party route/service-point assignment is cleared so that the parcel can be reassigned within MAKOS.

## Route data

The seed command retains the previously selected origin/destination pairs and associates them with MAKOS SACCO. Duplicate origin/destination pairs are naturally represented once because each operator route is unique by operator, origin and destination.

The route list is an administrator-provided configuration. Its presence in the database is not independent evidence that a particular journey is currently operating. MAKOS staff should confirm each route before dispatching parcels.

## Kenya destinations

The Kenya destination seed creates the 47 counties and the configured starter towns. Town availability is used for parcel registration; it does not mean every town has a staffed MAKOS branch. Branch records should be maintained separately and linked to their actual towns.

## Setup

Run migrations, then seed destinations before MAKOS routes:

```powershell
python manage.py migrate
python manage.py seed_kenya_destinations
python manage.py seed_published_operator_routes
```

The route seed configures MAKOS SACCO as the only operator and removes legacy third-party operator records and their routes/service points. It preserves parcels and tracking history.

