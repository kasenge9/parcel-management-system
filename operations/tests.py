from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
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
        cls.customer = get_user_model().objects.create_user(username="customer", password="StrongPass!234")
        cls.customer.groups.add(Group.objects.get(name="Customer"))
        cls.admin = get_user_model().objects.create_superuser(username="root", email="root@example.com", password="StrongPass!234")

    def test_anonymous_staff_page_redirects_to_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_customer_role_cannot_access_staff_dashboard(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)

    def test_clerk_can_access_dashboard_and_register_parcels(self):
        self.client.force_login(self.clerk)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("parcel_create")).status_code, 200)

    def test_clerk_cannot_manage_user_accounts(self):
        self.client.force_login(self.clerk)
        self.assertEqual(self.client.get(reverse("staff_users")).status_code, 403)

    def test_superuser_can_manage_accounts(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("staff_users")).status_code, 200)

    def test_roles_are_defined(self):
        self.assertEqual(set(ROLE_PERMISSIONS), {"System Administrator", "Branch Manager", "Parcel Clerk", "Dispatcher", "Driver", "Finance Officer", "Customer"})
