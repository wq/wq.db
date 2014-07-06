from django.apps import AppConfig


# Avoid label conflict with django.contrib.auth in Django 1.7
class AuthAppConfig(AppConfig):
    name = 'wq.db.rest.auth'
    label = 'wq_auth'
