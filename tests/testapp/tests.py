from rest_framework.test import APITestCase
from rest_framework import status
from .models import RootModel
import json


class TestCase(APITestCase):
    def setUp(self):
        instance = RootModel.objects.find('instance')
        instance.description = "Test"
        instance.save()

    def test_list_at_root(self):
        response = self.client.get("/.json")
        self.assertTrue(status.is_success(response.status_code))
        self.assertTrue(len(response.data['list']) == 1)

    def test_detail_at_root(self):
        response = self.client.get('/instance.json')
        self.assertTrue(status.is_success(response.status_code))
        self.assertTrue(response.data['description'] == "Test")
