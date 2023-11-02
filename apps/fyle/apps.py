from django.apps import AppConfig


class FyleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.fyle"

    def ready(self):
        super(FyleConfig, self).ready()
        import apps.fyle.signals # noqa
