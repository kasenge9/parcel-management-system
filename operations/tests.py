from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
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
        from django.db.models import ProtectedError

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
