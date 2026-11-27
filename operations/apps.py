from django.apps import AppConfig


class OperationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "operations"

    def ready(self):
        # Importing registers the post_migrate receiver for standard role groups.
        from . import roles  # noqa: F401
