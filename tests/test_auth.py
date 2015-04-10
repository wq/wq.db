from rest_framework.test import APITestCase
import json

from django.contrib.auth.models import User


class AuthTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.user.social_auth.create(
            provider="google",
            uid="testuser@example.com",
        )
        self.client.force_authenticate(self.user)

    def test_auth_config_json(self):
        response = self.client.get('/config.json')
        result = json.loads(response.content.decode('utf-8'))
        self.assertTrue("login" in result['pages'])

    def test_auth_login_info(self):
        response = self.client.get('/login.json')
        result = json.loads(response.content.decode('utf-8'))
        self.assertTrue("user" in result)
        self.assertTrue("social_auth" in result['user'])
        account = result['user']['social_auth']['accounts'][0]

        self.assertEqual(account['label'], "testuser@example.com")
        self.assertEqual(account['provider_label'], 'Google')

    def test_auth_context_processors(self):
        response = self.client.get('/auth_context')
        result = response.content.decode('utf-8')
        self.assertHTMLEqual(
            result,
            """
            <div>
                <p>testuser</p>
                <ul>
                  <li>Google - testuser@example.com</li>
                </ul>
            </div>
            """
        )
