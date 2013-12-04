from django.test import TestCase, Client
import json


class RestTestCase(TestCase):
    def test_config_json(self):
        response = self.client.get('/config.json')
        result = json.loads(response.content)
        self.assertTrue("pages" in result)
