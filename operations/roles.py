from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver


# Django's built-in model permissions are the policy primitives. Roles are
# groups, so membership changes take effect immediately without a custom user
# model or a risky user-table migration.
ROLE_PERMISSIONS = {
    "System Administrator": "all",
    "Branch Manager": {
        "parcel": ("view", "add", "change", "delete"),
        "customer": ("view", "add", "change"),
        "branch": ("view", "change"),
        "trackingevent": ("view", "add", "change"),
        "payment": ("view", "add", "change"),
        "vehicle": ("view", "add", "change"),
        "driver": ("view", "add", "change"),
        "dispatch": ("view", "add", "change"),
        "dispatchitem": ("view", "add", "change"),
    },
    "Parcel Clerk": {
        "parcel": ("view", "add", "change"),
        "customer": ("view", "add", "change"),
        "branch": ("view",),
        "trackingevent": ("view", "add"),
        "payment": ("view",),
    },
    "Dispatcher": {
        "parcel": ("view", "change"),
        "branch": ("view",),
        "trackingevent": ("view", "add"),
        "vehicle": ("view", "change"),
        "driver": ("view", "change"),
        "dispatch": ("view", "add", "change"),
        "dispatchitem": ("view", "add", "change"),
    },
    "Driver": {
        "parcel": ("view",),
        "trackingevent": ("view", "add"),
        "dispatch": ("view",),
        "dispatchitem": ("view",),
    },
    "Finance Officer": {
        "parcel": ("view",),
        "customer": ("view",),
        "branch": ("view",),
        "payment": ("view", "add", "change"),
    },
    # Customer accounts are intentionally not given staff-operation access.
    "Customer": {},
}


def role_names():
    return tuple(ROLE_PERMISSIONS)


def sync_role_groups(sender, **kwargs):
    """Create the standard roles and keep their app permissions declarative."""
    permissions = Permission.objects.filter(content_type__app_label="operations")
    for role, policy in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=role)
        if policy == "all":
            selected = permissions
        else:
            codenames = [
                f"{action}_{model}"
                for model, actions in policy.items()
                for action in actions
            ]
            selected = permissions.filter(codename__in=codenames)
        group.permissions.set(selected)


@receiver(post_migrate, dispatch_uid="operations.sync_role_groups")
def create_role_groups(sender, **kwargs):
    if sender.label == "operations":
        sync_role_groups(sender=sender, **kwargs)
