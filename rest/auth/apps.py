from django.apps import AppConfig


# Avoid label conflict with django.contrib.auth
class AuthAppConfig(AppConfig):
    name = 'wq.db.rest.auth'
    label = 'wq_auth'
