from rest_framework.test import APITestCase, APIClient
from django.conf import settings


class APIClient(APIClient):
    def generic(self, method, path, *args, **kwargs):
        """
        Equivalent toplemented method.

        Args:
            self: (todo): write your description
            method: (str): write your description
            path: (str): write your description
        """
        if settings.WITH_NONROOT:
            path = '/wqsite' + path
        return super().generic(method, path, *args, **kwargs)


class APITestCase(APITestCase):
    client_class = APIClient
