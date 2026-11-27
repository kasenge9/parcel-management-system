from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

ROLE_PERMISSIONS = {
    "Administrator": "all",
    "Management": {"branch": ("view",), "customer": ("view",), "parcel": ("view",), "trackingevent": ("view",), "payment": ("view",), "vehicle": ("view",), "driver": ("view",), "dispatch": ("view",), "dispatchitem": ("view",)},
    "Clerk": {"branch": ("view",), "customer": ("add", "view", "change"), "parcel": ("add", "view"), "trackingevent": ("view",)},
    "Dispatcher": {"branch": ("view",), "parcel": ("view",), "trackingevent": ("view",), "vehicle": ("view",), "driver": ("view",), "dispatch": ("add", "view", "change"), "dispatchitem": ("add", "view", "change")},
}

def setup_default_roles():
    content_types = ContentType.objects.filter(app_label="operations")
    all_permissions = Permission.objects.filter(content_type__in=content_types)
    for role_name, rules in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=role_name)
        if rules == "all":
            group.permissions.set(all_permissions)
            continue
        selected = []
        for model_name, actions in rules.items():
            content_type = content_types.filter(model=model_name).first()
            if content_type is None:
                continue
            codenames = [f"{action}_{model_name}" for action in actions]
            selected.extend(Permission.objects.filter(content_type=content_type, codename__in=codenames))
        group.permissions.set(selected)
