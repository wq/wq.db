from .base import APITestCase
from django.core.exceptions import ImproperlyConfigured
try:
    from django.urls import include
except ImportError:
    from django.conf.urls import include


class RestRouterTestCase(APITestCase):
    def test_rest_model_conflict(self):
        from wq.db import rest
        from tests.conflict_app.models import Item

        # Register model with same name as existing model
        with self.assertRaises(ImproperlyConfigured) as e:
            rest.router.register_model(Item, fields="__all__")
        self.assertEqual(
            e.exception.args[0],
            "Could not register <class 'tests.conflict_app.models.Item'>: "
            "the name 'item' was already registered for "
            "<class 'tests.rest_app.models.Item'>"
        )
        self.assertNotIn(Item, rest.router._models)

        # Register model with different name, but same URL as existing model
        with self.assertRaises(ImproperlyConfigured) as e:
            rest.router.register_model(
                Item, name="conflictitem", fields="__all__"
            )
        self.assertEqual(
            e.exception.args[0],
            "Could not register <class 'tests.conflict_app.models.Item'>: "
            "the url 'items' was already registered for "
            "<class 'tests.rest_app.models.Item'>"
        )
        self.assertNotIn(Item, rest.router._models)

        # Register model with different name and URL
        rest.router.register_model(
            Item, name="conflictitem", url="conflictitems", fields="__all__"
        )
        self.assertIn(Item, rest.router._models)
        self.assertIn("conflictitem", rest.router.get_config()['pages'])

    def test_rest_old_config(self):
        from wq.db import rest
        from tests.conflict_app.models import TestModel

        with self.assertRaises(ImproperlyConfigured):
            rest.router.register_model(
                TestModel,
                partial=True,
                fields="__all__"
            )

        self.assertNotIn(TestModel, rest.router._models)

        with self.assertRaises(ImproperlyConfigured):
            rest.router.register_model(
                TestModel,
                reversed=True,
                fields="__all__"
            )

        self.assertNotIn(TestModel, rest.router._models)

        with self.assertRaises(ImproperlyConfigured):
            rest.router.register_model(
                TestModel,
                max_local_pages=0,
                fields="__all__"
            )

        self.assertNotIn(TestModel, rest.router._models)

    def test_rest_include(self):
        from wq.db import rest
        include(rest.router.urls)
