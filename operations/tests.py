from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Branch,
    Customer,
    Dispatch,
    Driver,
    Parcel,
    Payment,
    TrackingEvent,
    TransportOperator,
    OperatorRoute,
    OperatorServicePoint,
    County,
    Town,
    Vehicle,
)
from .roles import ROLE_PERMISSIONS, sync_role_groups


class PublicWebsitePagesTests(TestCase):
    def test_homepage_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Every parcel has")

    def test_about_page_loads(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A more connected parcel journey")

    def test_services_page_loads(self):
        response = self.client.get(reverse("services"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tools for every stage")

    def test_branches_page_loads(self):
        response = self.client.get(reverse("branches"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Branches")

    def test_contact_page_loads(self):
        response = self.client.get(reverse("contact"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contact MAKOS SACCO")

    def test_tracking_page_loads(self):
        response = self.client.get(reverse("track"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Track your parcel")


class RoleBasedAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        sync_role_groups(sender=None)
        cls.clerk = get_user_model().objects.create_user(
            username="clerk", password="StrongPass!234"
        )
        cls.clerk.groups.add(Group.objects.get(name="Parcel Clerk"))
        cls.dispatcher = get_user_model().objects.create_user(
            username="dispatcher", password="StrongPass!234"
        )
        cls.dispatcher.groups.add(Group.objects.get(name="Dispatcher"))
        cls.manager = get_user_model().objects.create_user(
            username="manager", password="StrongPass!234"
        )
        cls.manager.groups.add(Group.objects.get(name="Branch Manager"))
        cls.customer = get_user_model().objects.create_user(
            username="customer", password="StrongPass!234"
        )
        cls.customer.groups.add(Group.objects.get(name="Customer"))
        cls.admin = get_user_model().objects.create_superuser(
            username="root", email="root@example.com", password="StrongPass!234"
        )

    def test_anonymous_staff_page_redirects_to_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('dashboard')}"
        )

    def test_customer_login_returns_to_public_home(self):
        response = self.client.post(
            reverse("login"),
            {"username": "customer", "password": "StrongPass!234"},
        )
        self.assertRedirects(response, reverse("home"))

    def test_customer_role_cannot_access_staff_dashboard(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)

    def test_clerk_can_access_dashboard_and_register_parcels(self):
        self.client.force_login(self.clerk)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("parcel_create")).status_code, 200)

    def test_clerk_cannot_update_parcel_status(self):
        self.client.force_login(self.clerk)
        response = self.client.post(
            reverse("update_status", args=[1]), {"status": "in_transit"}
        )
        self.assertEqual(response.status_code, 403)

    def test_dispatcher_cannot_open_management_portal(self):
        self.client.force_login(self.dispatcher)
        self.assertEqual(
            self.client.get(reverse("management_dashboard")).status_code, 403
        )

    def test_branch_manager_can_open_management_portal(self):
        self.client.force_login(self.manager)
        self.assertEqual(
            self.client.get(reverse("management_dashboard")).status_code, 200
        )

    def test_clerk_cannot_manage_user_accounts(self):
        self.client.force_login(self.clerk)
        self.assertEqual(self.client.get(reverse("staff_users")).status_code, 403)

    def test_superuser_can_manage_accounts(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("staff_users")).status_code, 200)

    def test_roles_are_defined(self):
        self.assertEqual(
            set(ROLE_PERMISSIONS),
            {
                "System Administrator",
                "Branch Manager",
                "Parcel Clerk",
                "Dispatcher",
                "Driver",
                "Finance Officer",
                "Customer",
            },
        )


class OperationsModelValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.origin = Branch.objects.create(name="Mombasa", location="Mombasa")
        cls.destination = Branch.objects.create(
            name="Nairobi", location="Nairobi"
        )
        cls.sender = Customer.objects.create(
            full_name="Amina Sender", phone="+254700000001"
        )
        cls.recipient = Customer.objects.create(
            full_name="Brian Recipient", phone="+254700000002"
        )
        cls.parcel = Parcel.objects.create(
            sender=cls.sender,
            recipient=cls.recipient,
            description="Documents",
            weight_kg=Decimal("1.50"),
            origin=cls.origin,
            destination=cls.destination,
            delivery_fee=Decimal("250.00"),
        )

    def test_tracking_number_is_generated_unique_and_indexed(self):
        second_parcel = Parcel.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            description="Small package",
            weight_kg=Decimal("0.50"),
            origin=self.origin,
            destination=self.destination,
            delivery_fee=Decimal("100.00"),
        )
        field = Parcel._meta.get_field("tracking_number")
        self.assertTrue(field.unique)
        self.assertTrue(field.db_index)
        self.assertTrue(self.parcel.tracking_number.startswith("MK"))
        self.assertEqual(len(self.parcel.tracking_number), 12)
        self.assertNotEqual(self.parcel.tracking_number, second_parcel.tracking_number)

    def test_duplicate_tracking_number_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Parcel.objects.create(
                    tracking_number=self.parcel.tracking_number,
                    sender=self.sender,
                    recipient=self.recipient,
                    description="Duplicate code",
                    weight_kg=Decimal("1.00"),
                    origin=self.origin,
                    destination=self.destination,
                    delivery_fee=Decimal("10.00"),
                )

    def test_parcel_model_validation_rejects_nonpositive_weight(self):
        self.parcel.weight_kg = Decimal("0.00")
        with self.assertRaises(ValidationError) as raised:
            self.parcel.full_clean()
        self.assertIn("weight_kg", raised.exception.message_dict)

    def test_parcel_database_rejects_nonpositive_weight(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Parcel.objects.create(
                    sender=self.sender,
                    recipient=self.recipient,
                    description="Invalid weight",
                    weight_kg=Decimal("0.00"),
                    origin=self.origin,
                    destination=self.destination,
                    delivery_fee=Decimal("10.00"),
                )

    def test_parcel_database_rejects_negative_delivery_fee(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Parcel.objects.create(
                    sender=self.sender,
                    recipient=self.recipient,
                    description="Invalid fee",
                    weight_kg=Decimal("1.00"),
                    origin=self.origin,
                    destination=self.destination,
                    delivery_fee=Decimal("-0.01"),
                )

    def test_payment_must_be_greater_than_zero(self):
        payment = Payment(
            parcel=self.parcel,
            amount=Decimal("0.00"),
            method=Payment.Method.CASH,
        )
        with self.assertRaises(ValidationError):
            payment.full_clean()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                payment.save(force_insert=True)

    def test_dispatch_arrival_cannot_precede_departure(self):
        departure = timezone.now()
        dispatch = Dispatch(
            vehicle=Vehicle.objects.create(registration_number="KDA 123A"),
            driver=Driver.objects.create(
                full_name="Test Driver", phone="+254700000003"
            ),
            origin=self.origin,
            destination=self.destination,
            departure_time=departure,
            arrived_at=departure - timedelta(minutes=1),
        )
        with self.assertRaises(ValidationError):
            dispatch.full_clean()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                dispatch.save(force_insert=True)

    def test_required_customer_fields_reject_whitespace(self):
        customer = Customer(full_name="   ", phone="   ")
        with self.assertRaises(ValidationError) as raised:
            customer.full_clean()
        self.assertIn("full_name", raised.exception.message_dict)
        self.assertIn("phone", raised.exception.message_dict)

    def test_required_fields_are_non_nullable(self):
        for model, field_names in (
            (Customer, ("full_name", "phone")),
            (Parcel, ("sender", "recipient", "description", "weight_kg")),
            (Payment, ("parcel", "amount", "method")),
            (Dispatch, ("vehicle", "driver", "origin", "destination")),
        ):
            for field_name in field_names:
                with self.subTest(model=model.__name__, field=field_name):
                    self.assertFalse(model._meta.get_field(field_name).null)

    def test_customer_cannot_be_deleted_while_parcels_reference_them(self):
        with self.assertRaises(ProtectedError):
            self.sender.delete()

    def test_tracking_events_are_deleted_with_their_parcel(self):
        event = TrackingEvent.objects.create(
            parcel=self.parcel,
            status=Parcel.Status.REGISTERED,
            location="Mombasa",
        )
        parcel_id = self.parcel.pk
        self.parcel.delete()
        self.assertFalse(TrackingEvent.objects.filter(pk=event.pk).exists())
        self.assertFalse(Parcel.objects.filter(pk=parcel_id).exists())



class ForeignKeyDeletionPolicyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.origin = Branch.objects.create(name="Policy Origin", location="Mombasa")
        cls.destination = Branch.objects.create(
            name="Policy Destination", location="Nairobi"
        )
        cls.sender = Customer.objects.create(
            full_name="Policy Sender", phone="+254711111111"
        )
        cls.recipient = Customer.objects.create(
            full_name="Policy Recipient", phone="+254722222222"
        )
        cls.parcel = Parcel.objects.create(
            sender=cls.sender,
            recipient=cls.recipient,
            description="Policy test parcel",
            weight_kg=Decimal("2.00"),
            origin=cls.origin,
            destination=cls.destination,
            delivery_fee=Decimal("50.00"),
        )

    def test_payment_protects_parcel_from_deletion(self):
        Payment.objects.create(
            parcel=self.parcel,
            amount=Decimal("50.00"),
            method=Payment.Method.CASH,
        )
        with self.assertRaises(ProtectedError):
            self.parcel.delete()

    def test_branch_is_protected_while_referenced_by_parcel(self):
        with self.assertRaises(ProtectedError):
            self.origin.delete()

    def test_user_deletion_sets_tracking_and_payment_user_to_null(self):
        user = get_user_model().objects.create_user(
            username="recording-user", password="StrongPass!234"
        )
        event = TrackingEvent.objects.create(
            parcel=self.parcel,
            status=Parcel.Status.REGISTERED,
            created_by=user,
        )
        payment = Payment.objects.create(
            parcel=self.parcel,
            amount=Decimal("50.00"),
            method=Payment.Method.CASH,
            received_by=user,
        )

        user.delete()
        event.refresh_from_db()
        payment.refresh_from_db()
        self.assertIsNone(event.created_by)
        self.assertIsNone(payment.received_by)

    def test_dispatch_deletion_cascades_to_dispatch_items(self):
        dispatch = Dispatch.objects.create(
            vehicle=Vehicle.objects.create(registration_number="KDB 456B"),
            driver=Driver.objects.create(
                full_name="Policy Driver", phone="+254733333333"
            ),
            origin=self.origin,
            destination=self.destination,
        )
        dispatch.parcels.add(self.parcel)
        self.assertEqual(dispatch.dispatch_items.count(), 1)

        dispatch.delete()
        self.assertFalse(
            Dispatch.objects.filter(pk=dispatch.pk).exists()
        )
        self.assertFalse(
            self.parcel.dispatch_items.exists()
        )

    def test_dispatch_item_protects_parcel_until_dispatch_is_removed(self):
        dispatch = Dispatch.objects.create(
            vehicle=Vehicle.objects.create(registration_number="KDC 789C"),
            driver=Driver.objects.create(
                full_name="Second Policy Driver", phone="+254744444444"
            ),
            origin=self.origin,
            destination=self.destination,
        )
        dispatch.parcels.add(self.parcel)

        with self.assertRaises(ProtectedError):
            self.parcel.delete()

        dispatch.delete()
        parcel_id = self.parcel.pk
        self.parcel.delete()
        self.assertFalse(Parcel.objects.filter(pk=parcel_id).exists())



class ParcelTrackingWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        sync_role_groups(sender=None)
        cls.origin = Branch.objects.create(name="Tracking Mombasa", location="Mombasa")
        cls.destination = Branch.objects.create(name="Tracking Nairobi", location="Nairobi")
        cls.sender = Customer.objects.create(full_name="Sender Person", phone="+254700000001")
        cls.recipient = Customer.objects.create(full_name="Recipient Person", phone="+254700000002")
        cls.parcel = Parcel.objects.create(sender=cls.sender, recipient=cls.recipient, description="Documents", weight_kg=Decimal("1.00"), origin=cls.origin, destination=cls.destination, delivery_fee=Decimal("150.00"))
        cls.dispatcher = get_user_model().objects.create_user(username="tracking-dispatcher", password="StrongPass!234")
        cls.dispatcher.groups.add(Group.objects.get(name="Dispatcher"))
        cls.clerk = get_user_model().objects.create_user(username="tracking-clerk", password="StrongPass!234")
        cls.clerk.groups.add(Group.objects.get(name="Parcel Clerk"))

    def test_dispatcher_can_record_status_location_and_note(self):
        self.client.force_login(self.dispatcher)
        response = self.client.post(reverse("update_status", args=[self.parcel.pk]), {"status": Parcel.Status.IN_TRANSIT, "location": "Voi transit stop", "note": "Vehicle departed Mombasa"})
        self.assertEqual(response.status_code, 302)
        self.parcel.refresh_from_db()
        event = self.parcel.tracking_events.get()
        self.assertEqual(self.parcel.status, Parcel.Status.IN_TRANSIT)
        self.assertEqual(event.location, "Voi transit stop")
        self.assertEqual(event.note, "Vehicle departed Mombasa")
        self.assertEqual(event.created_by, self.dispatcher)

    def test_invalid_status_does_not_change_parcel(self):
        self.client.force_login(self.dispatcher)
        self.client.post(reverse("update_status", args=[self.parcel.pk]), {"status": "invalid", "location": "Voi", "note": "Invalid"})
        self.parcel.refresh_from_db()
        self.assertEqual(self.parcel.status, Parcel.Status.REGISTERED)
        self.assertEqual(self.parcel.tracking_events.count(), 0)

    def test_duplicate_status_does_not_create_event(self):
        self.client.force_login(self.dispatcher)
        self.client.post(reverse("update_status", args=[self.parcel.pk]), {"status": Parcel.Status.REGISTERED, "location": "Mombasa", "note": ""})
        self.assertEqual(self.parcel.tracking_events.count(), 0)

    def test_parcel_clerk_cannot_write_tracking_updates(self):
        self.client.force_login(self.clerk)
        response = self.client.post(reverse("update_status", args=[self.parcel.pk]), {"status": Parcel.Status.IN_TRANSIT, "location": "Voi", "note": ""})
        self.assertEqual(response.status_code, 403)
        self.parcel.refresh_from_db()
        self.assertEqual(self.parcel.status, Parcel.Status.REGISTERED)

    def test_public_tracking_displays_notes_but_not_private_contacts(self):
        TrackingEvent.objects.create(parcel=self.parcel, status=Parcel.Status.REGISTERED, location="Mombasa", note="Parcel accepted")
        response = self.client.post(reverse("track"), {"tracking_number": self.parcel.tracking_number.lower()})
        self.assertContains(response, "Parcel accepted")
        self.assertNotContains(response, self.sender.phone)
        self.assertNotContains(response, self.recipient.phone)



class KenyaDestinationDirectoryTests(TestCase):
    def test_destination_page_loads(self):
        response = self.client.get(reverse("destinations"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Destinations across Kenya")

    def test_route_cannot_be_activated_without_verification(self):
        county = County.objects.create(name="Test County", code=99)
        origin = Town.objects.create(county=county, name="Origin")
        destination = Town.objects.create(county=county, name="Destination")
        operator = TransportOperator.objects.create(
            name="Test Coach", category=TransportOperator.Category.PASSENGER
        )
        route = OperatorRoute(
            operator=operator, origin=origin, destination=destination,
            service_type=TransportOperator.Category.PASSENGER, is_active=True,
        )
        with self.assertRaises(ValidationError):
            route.full_clean()

    def test_passenger_route_does_not_assume_parcel_acceptance(self):
        county = County.objects.create(name="Sample County", code=98)
        origin = Town.objects.create(county=county, name="Sample Origin")
        destination = Town.objects.create(county=county, name="Sample Destination")
        operator = TransportOperator.objects.create(
            name="Sample Coach", category=TransportOperator.Category.PASSENGER
        )
        route = OperatorRoute.objects.create(
            operator=operator, origin=origin, destination=destination,
            service_type=TransportOperator.Category.PASSENGER,
            verification_status=OperatorRoute.Verification.PUBLISHED,
            is_active=True,
        )
        self.assertFalse(route.parcel_service_confirmed)


class ParcelRegistrationDestinationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        sync_role_groups(sender=None)
        cls.clerk = get_user_model().objects.create_user(
            username="destination-clerk", password="StrongPass!234"
        )
        cls.clerk.groups.add(Group.objects.get(name="Parcel Clerk"))
        cls.county = County.objects.create(name="Registration County", code=97)
        cls.origin_town = Town.objects.create(county=cls.county, name="Dispatch Town")
        cls.town = Town.objects.create(county=cls.county, name="Registration Town")
        cls.origin = Branch.objects.create(
            name="Registration Origin", location="Origin town", town=cls.origin_town
        )

    def registration_payload(self, sender_phone, recipient_phone, **extra):
        payload = {
            "sender_name": "Sender One",
            "sender_phone": sender_phone,
            "recipient_name": "Recipient One",
            "recipient_phone": recipient_phone,
            "description": "Documents",
            "weight_kg": "1.25",
            "origin": self.origin.pk,
            "destination_county": self.county.pk,
            "destination_town": self.town.pk,
            "delivery_fee": "100.00",
        }
        payload.update(extra)
        return payload

    def test_parcel_can_be_registered_without_route_assignment(self):
        self.client.force_login(self.clerk)
        response = self.client.post(
            reverse("parcel_create"),
            self.registration_payload("+254700111111", "+254700222222"),
        )
        self.assertEqual(response.status_code, 302)
        parcel = Parcel.objects.get(sender__phone="+254700111111")
        self.assertEqual(parcel.destination_town, self.town)
        self.assertIsNone(parcel.destination)
        self.assertIsNone(parcel.operator_route)
        self.assertEqual(parcel.route_assignment_status, "awaiting_route_assignment")

    def test_registration_accepts_matching_verified_parcel_route(self):
        operator = TransportOperator.objects.create(
            name="Confirmed Courier",
            category=TransportOperator.Category.COURIER,
            parcel_service_confirmed=True,
        )
        route = OperatorRoute.objects.create(
            operator=operator,
            origin=self.origin_town,
            destination=self.town,
            service_type=TransportOperator.Category.COURIER,
            verification_status=OperatorRoute.Verification.CONFIRMED,
            parcel_service_confirmed=True,
            is_active=True,
        )
        self.client.force_login(self.clerk)
        response = self.client.post(
            reverse("parcel_create"),
            self.registration_payload(
                "+254700333333", "+254700444444", operator_route=route.pk
            ),
        )
        self.assertEqual(response.status_code, 302)
        parcel = Parcel.objects.get(sender__phone="+254700333333")
        self.assertEqual(parcel.operator_route, route)
        self.assertEqual(parcel.route_assignment_status, "assigned")

    def test_registration_can_select_verified_receiving_courier_point(self):
        operator = TransportOperator.objects.create(
            name="Fargo Test Courier",
            category=TransportOperator.Category.COURIER,
            parcel_service_confirmed=True,
        )
        service_point = OperatorServicePoint.objects.create(
            operator=operator,
            town=self.town,
            source_url="https://example.com/branches",
            is_verified=True,
            accepts_parcels=True,
            is_active=True,
        )
        self.client.force_login(self.clerk)
        response = self.client.post(
            reverse("parcel_create"),
            self.registration_payload(
                "+254700777777", "+254700888888",
                operator_service_point=service_point.pk,
            ),
        )
        self.assertEqual(response.status_code, 302)
        parcel = Parcel.objects.get(sender__phone="+254700777777")
        self.assertEqual(parcel.operator_service_point, service_point)
        self.assertIsNone(parcel.operator_route)
        self.assertEqual(parcel.route_assignment_status, "awaiting_route_assignment")

    def test_registration_rejects_route_for_different_destination(self):
        operator = TransportOperator.objects.create(
            name="Another Courier",
            category=TransportOperator.Category.COURIER,
            parcel_service_confirmed=True,
        )
        other_town = Town.objects.create(county=self.county, name="Other Town")
        route = OperatorRoute.objects.create(
            operator=operator,
            origin=self.origin_town,
            destination=other_town,
            service_type=TransportOperator.Category.COURIER,
            verification_status=OperatorRoute.Verification.CONFIRMED,
            parcel_service_confirmed=True,
            is_active=True,
        )
        from .forms import ParcelForm
        form = ParcelForm(data=self.registration_payload(
            "+254700555555", "+254700666666", operator_route=route.pk
        ))
        self.assertFalse(form.is_valid())
        self.assertIn("operator_route", form.errors)
