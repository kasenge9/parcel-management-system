from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from .access import role_required
from .role_setup import setup_default_roles


@role_required("Clerk")
def clerk_only_view(request):
    from django.http import HttpResponse
    return HttpResponse("ok")


class RoleRequiredTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.clerk_group, _ = Group.objects.get_or_create(name="Clerk")

    def test_anonymous_user_is_redirected_to_login(self):
        request = self.factory.get("/protected/")
        request.user = AnonymousUser()

        response = clerk_only_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_user_without_required_role_gets_forbidden(self):
        user = User.objects.create_user(username="outsider", password="Strong-pass-123!")
        request = self.factory.get("/protected/")
        request.user = user

        with self.assertRaises(PermissionDenied):
            clerk_only_view(request)

    def test_user_in_required_group_is_allowed(self):
        user = User.objects.create_user(username="clerk", password="Strong-pass-123!")
        user.groups.add(self.clerk_group)
        request = self.factory.get("/protected/")
        request.user = user

        response = clerk_only_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_superuser_bypasses_role_check(self):
        user = User.objects.create_superuser(
            username="root", email="root@example.com", password="Strong-pass-123!"
        )
        request = self.factory.get("/protected/")
        request.user = user

        response = clerk_only_view(request)

        self.assertEqual(response.status_code, 200)


class DefaultRoleSetupTests(TestCase):
    def test_setup_creates_all_standard_groups(self):
        setup_default_roles()

        for name in ("Administrator", "Clerk", "Dispatcher", "Management"):
            with self.subTest(role=name):
                self.assertTrue(Group.objects.filter(name=name).exists())

    def test_setup_is_safe_to_run_more_than_once(self):
        setup_default_roles()
        setup_default_roles()

        self.assertEqual(
            Group.objects.filter(
                name__in=("Administrator", "Clerk", "Dispatcher", "Management")
            ).count(),
            4,
        )

    def test_clerk_receives_parcel_add_permission(self):
        setup_default_roles()
        clerk = Group.objects.get(name="Clerk")

        self.assertTrue(
            clerk.permissions.filter(codename="add_parcel").exists()
        )
