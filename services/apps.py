from django.apps import AppConfig


class ServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services'

    # def ready(self):
    #     from .models import Gender
    #     # Ensure Male & Female always exist
    #     if not Gender.objects.filter(name='male').exists():
    #         Gender.objects.create(name='male')
    #     if not Gender.objects.filter(name='female').exists():
    #         Gender.objects.create(name='female')

