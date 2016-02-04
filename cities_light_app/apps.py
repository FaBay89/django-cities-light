from django.apps import AppConfig


class CitiesLightAppConfig(AppConfig):
    name = 'cities_light_app'
    # verbose_name = "Cities Light App"

    def ready(self):
        import cities_light_app.signals.handlers
