from .base import APITestCase
import json

from django.contrib.auth.models import User


class AuthTestCase(APITestCase):
    def setUp(self):
        """
        Set the user s username and password.

        Args:
            self: (todo): write your description
        """
        self.user = User.objects.create(username="testuser")
        self.client.force_authenticate(self.user)

    def test_auth_config_json(self):
        """
        Test if the json config is valid.

        Args:
            self: (todo): write your description
        """
        response = self.client.get('/config.json')
        result = json.loads(response.content.decode('utf-8'))
        self.assertTrue("login" in result['pages'])

    def test_auth_login_info(self):
        """
        Perform login info.

        Args:
            self: (todo): write your description
        """
        response = self.client.get('/login.json')
        result = json.loads(response.content.decode('utf-8'))
        self.assertTrue("user" in result)

    def test_auth_context_processors(self):
        """
        Method to process process context.

        Args:
            self: (todo): write your description
        """
        response = self.client.get('/auth_context')
        result = response.content.decode('utf-8')
        self.assertHTMLEqual(
            result,
            """
            <div>
                <p>testuser</p>
            </div>
            """
        )
