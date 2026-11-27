from django.test import TestCase
from django.urls import reverse


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
