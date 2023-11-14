from django.apps import AppConfig


class MappingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.mappings"

    def ready(self):
        super(MappingsConfig, self).ready()
        import apps.mappings.signals # noqa
