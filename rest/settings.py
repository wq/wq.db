from django.core.exceptions import ImproperlyConfigured

raise ImproperlyConfigured("""
wq.db.rest.settings has been renamed to wq.db.default_settings.
Please update your configuration.
See https://wq.io/wq.db/releases/v0.8.0 for more information.
""")
