from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from decimal import Decimal

from .forms import ParcelForm
from .models import Branch, Customer, Parcel, TrackingEvent
from django.urls import reverse

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
        cls.clerk = get_user_model().objects.create_user(username="clerk", password="StrongPass!234")
        cls.clerk.groups.add(Group.objects.get(name="Parcel Clerk"))
        cls.dispatcher = get_user_model().objects.create_user(username="dispatcher", password="StrongPass!234")
        cls.dispatcher.groups.add(Group.objects.get(name="Dispatcher"))
        cls.manager = get_user_model().objects.create_user(username="manager", password="StrongPass!234")
        cls.manager.groups.add(Group.objects.get(name="Branch Manager"))
        cls.customer = get_user_model().objects.create_user(username="customer", password="StrongPass!234")
        cls.customer.groups.add(Group.objects.get(name="Customer"))
        cls.admin = get_user_model().objects.create_superuser(username="root", email="root@example.com", password="StrongPass!234")

    def test_anonymous_staff_page_redirects_to_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_customer_login_returns_to_public_home(self):
        response = self.client.post(reverse("login"), {"username": "customer", "password": "StrongPass!234"})
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
        response = self.client.post(reverse("update_status", args=[1]), {"status": "in_transit"})
        self.assertEqual(response.status_code, 403)

    def test_dispatcher_can_view_management_not_management_portal(self):
        self.client.force_login(self.dispatcher)
        self.assertEqual(self.client.get(reverse("management_dashboard")).status_code, 403)

    def test_branch_manager_can_open_management_portal(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("management_dashboard")).status_code, 200)

    def test_clerk_cannot_manage_user_accounts(self):
        self.client.force_login(self.clerk)
        self.assertEqual(self.client.get(reverse("staff_users")).status_code, 403)

    def test_superuser_can_manage_accounts(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("staff_users")).status_code, 200)

    def test_roles_are_defined(self):
        self.assertEqual(set(ROLE_PERMISSIONS), {"System Administrator", "Branch Manager", "Parcel Clerk", "Dispatcher", "Driver", "Finance Officer", "Customer"})



class ParcelRegistrationWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        sync_role_groups(sender=None)
        cls.clerk = get_user_model().objects.create_user(
            username="registration-clerk", password="StrongPass!234"
        )
        cls.clerk.groups.add(Group.objects.get(name="Parcel Clerk"))
        cls.origin = Branch.objects.create(name="Mombasa Central", location="Mombasa")
        cls.destination = Branch.objects.create(name="Nairobi", location="Nairobi")

    def valid_registration_data(self, **overrides):
        data = {
            "sender_name": "Amina Sender",
            "sender_phone": "+254700111222",
            "recipient_name": "Brian Recipient",
            "recipient_phone": "+254711222333",
            "description": "Electrical components",
            "weight_kg": "2.50",
            "origin": str(self.origin.pk),
            "destination": str(self.destination.pk),
            "delivery_fee": "350.00",
        }
        data.update(overrides)
        return data

    def test_parcel_registration_creates_parcel_customers_and_first_event(self):
        self.client.force_login(self.clerk)
        response = self.client.post(
            reverse("parcel_create"), self.valid_registration_data()
        )

        self.assertEqual(response.status_code, 302)
        parcel = Parcel.objects.get()
        self.assertEqual(parcel.sender.full_name, "Amina Sender")
        self.assertEqual(parcel.recipient.full_name, "Brian Recipient")
        self.assertTrue(parcel.tracking_number.startswith("MK"))
        event = TrackingEvent.objects.get(parcel=parcel)
        self.assertEqual(event.status, Parcel.Status.REGISTERED)
        self.assertEqual(event.location, self.origin.name)
        self.assertEqual(event.note, "Parcel registered")
        self.assertEqual(event.created_by, self.clerk)

    def test_registration_reuses_existing_customer_by_phone(self):
        existing = Customer.objects.create(
            full_name="Existing Sender Name", phone="+254700111222"
        )
        self.client.force_login(self.clerk)
        response = self.client.post(
            reverse("parcel_create"), self.valid_registration_data()
        )

        self.assertEqual(response.status_code, 302)
        parcel = Parcel.objects.get()
        self.assertEqual(parcel.sender, existing)
        self.assertEqual(
            Customer.objects.filter(phone="+254700111222").count(), 1
        )
        self.assertEqual(parcel.sender.full_name, "Existing Sender Name")

    def test_registration_rejects_nonpositive_weight_and_negative_fee(self):
        form = ParcelForm(
            data=self.valid_registration_data(
                weight_kg="0",
                delivery_fee="-1.00",
            )
        )
        self.assertFalse(form.is_valid())
        self.assertIn("weight_kg", form.errors)
        self.assertIn("delivery_fee", form.errors)

    def test_registration_rejects_inactive_branch(self):
        inactive = Branch.objects.create(
            name="Closed Branch", location="Kilifi", is_active=False
        )
        form = ParcelForm(
            data=self.valid_registration_data(origin=str(inactive.pk))
        )
        self.assertFalse(form.is_valid())
        self.assertIn("origin", form.errors)

    def test_clerk_can_register_but_cannot_change_status(self):
        self.client.force_login(self.clerk)
        parcel = Parcel.objects.create(
            sender=Customer.objects.create(
                full_name="Sender", phone="+254700100001"
            ),
            recipient=Customer.objects.create(
                full_name="Recipient", phone="+254700100002"
            ),
            description="Test parcel",
            weight_kg=Decimal("1.00"),
            origin=self.origin,
            destination=self.destination,
            delivery_fee=Decimal("100.00"),
        )
        response = self.client.get(reverse("parcel_detail", args=[parcel.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Record a tracking update")
        response = self.client.post(
            reverse("update_status", args=[parcel.pk]),
            {"status": Parcel.Status.IN_TRANSIT},
        )
        self.assertEqual(response.status_code, 403)


class ParcelTrackingWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        sync_role_groups(sender=None)
        cls.dispatcher = get_user_model().objects.create_user(
            username="tracking-dispatcher", password="StrongPass!234"
        )
        cls.dispatcher.groups.add(Group.objects.get(name="Dispatcher"))
        cls.origin = Branch.objects.create(name="Tracking Mombasa", location="Mombasa")
        cls.destination = Branch.objects.create(name="Tracking Nairobi", location="Nairobi")
        cls.sender = Customer.objects.create(
            full_name="Private Sender", phone="+254799111222"
        )
        cls.recipient = Customer.objects.create(
            full_name="Private Recipient", phone="+254799333444"
        )
        cls.parcel = Parcel.objects.create(
            sender=cls.sender,
            recipient=cls.recipient,
            description="Private test parcel",
            weight_kg=Decimal("1.25"),
            origin=cls.origin,
            destination=cls.destination,
            delivery_fee=Decimal("250.00"),
        )

    def test_dispatcher_status_update_records_location_note_and_actor(self):
        self.client.force_login(self.dispatcher)
        response = self.client.post(
            reverse("update_status", args=[self.parcel.pk]),
            {
                "status": Parcel.Status.IN_TRANSIT,
                "location": "Mariakani transit point",
                "note": "Loaded onto vehicle KDA 123A",
            },
        )

        self.assertRedirects(
            response, reverse("parcel_detail", args=[self.parcel.pk])
        )
        self.parcel.refresh_from_db()
        self.assertEqual(self.parcel.status, Parcel.Status.IN_TRANSIT)
        event = TrackingEvent.objects.get(
            parcel=self.parcel, status=Parcel.Status.IN_TRANSIT
        )
        self.assertEqual(event.location, "Mariakani transit point")
        self.assertEqual(event.note, "Loaded onto vehicle KDA 123A")
        self.assertEqual(event.created_by, self.dispatcher)

    def test_status_update_rejects_invalid_status(self):
        self.client.force_login(self.dispatcher)
        self.client.post(
            reverse("update_status", args=[self.parcel.pk]),
            {"status": "teleported", "location": "Unknown"},
        )
        self.parcel.refresh_from_db()
        self.assertEqual(self.parcel.status, Parcel.Status.REGISTERED)
        self.assertFalse(
            TrackingEvent.objects.filter(
                parcel=self.parcel, status="teleported"
            ).exists()
        )

    def test_status_update_rejects_get_requests(self):
        self.client.force_login(self.dispatcher)
        response = self.client.get(
            reverse("update_status", args=[self.parcel.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_public_tracking_normalizes_code_and_hides_private_details_and_notes(self):
        TrackingEvent.objects.create(
            parcel=self.parcel,
            status=Parcel.Status.IN_TRANSIT,
            location="Mariakani",
            note="Internal note must remain private",
            created_by=self.dispatcher,
        )
        response = self.client.post(
            reverse("track"),
            {"tracking_number": self.parcel.tracking_number.lower()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.parcel.tracking_number)
        self.assertContains(response, "Mariakani")
        self.assertNotContains(response, self.sender.phone)
        self.assertNotContains(response, self.recipient.phone)
        self.assertNotContains(response, "Internal note must remain private")

    def test_tracking_history_is_presented_oldest_first(self):
        first = TrackingEvent.objects.create(
            parcel=self.parcel,
            status=Parcel.Status.REGISTERED,
            location="Mombasa",
        )
        second = TrackingEvent.objects.create(
            parcel=self.parcel,
            status=Parcel.Status.IN_TRANSIT,
            location="Voi",
        )
        response = self.client.post(
            reverse("track"),
            {"tracking_number": self.parcel.tracking_number},
        )
        html = response.content.decode()
        self.assertLess(html.index("Mombasa"), html.index("Voi"))
        self.assertLess(first.created_at, second.created_at)

    def test_staff_detail_displays_internal_tracking_notes(self):
        self.client.force_login(self.dispatcher)
        TrackingEvent.objects.create(
            parcel=self.parcel,
            status=Parcel.Status.REGISTERED,
            note="Internal handover check",
            created_by=self.dispatcher,
        )
        response = self.client.get(
            reverse("parcel_detail", args=[self.parcel.pk])
        )
        self.assertContains(response, "Internal handover check")

    def test_parcel_register_searches_sender_and_recipient(self):
        self.client.force_login(self.dispatcher)
        response = self.client.get(
            reverse("parcel_list"), {"q": "Private Recipient"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.parcel.tracking_number)

    def test_parcel_register_filters_by_status_and_paginates(self):
        self.client.force_login(self.dispatcher)
        response = self.client.get(
            reverse("parcel_list"),
            {"status": Parcel.Status.REGISTERED},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertContains(response, self.parcel.tracking_number)
