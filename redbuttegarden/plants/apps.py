from django.apps import AppConfig


class PlantsConfig(AppConfig):
    name = 'plants'

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        from . import signals
