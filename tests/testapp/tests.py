from rest_framework.test import APITestCase
from rest_framework import status
from .models import RootModel, AnnotatedModel
from wq.db.patterns.models import AnnotationType, Annotation
import json


class UrlsTestCase(APITestCase):
    def setUp(self):
        instance = RootModel.objects.find('instance')
        instance.description = "Test"
        instance.save()

    # Test url="" use case
    def test_list_at_root(self):
        response = self.client.get("/.json")
        self.assertTrue(status.is_success(response.status_code))
        self.assertTrue(len(response.data['list']) == 1)

    def test_detail_at_root(self):
        response = self.client.get('/instance.json')
        self.assertTrue(status.is_success(response.status_code))
        self.assertTrue(response.data['description'] == "Test")

    # Ensure nested serializers are created for SerializableGenericRelations
    # (e.g. identifiers), but only for detail views
    def test_detail_nested_identifiers(self):
        response = self.client.get('/instance.json')
        self.assertIn('identifiers', response.data)
        self.assertEqual(response.data['identifiers'][0]['slug'], 'instance')

    def test_list_nested_identifiers(self):
        response = self.client.get('/.json')
        self.assertNotIn('identifiers', response.data['list'][0])


class AnnotateTestCase(APITestCase):
    def setUp(self):
        AnnotationType.objects.create(name="Width")
        AnnotationType.objects.create(name="Height")

    def test_annotate_simple(self):
        instance = AnnotatedModel.objects.create(name="Test")
        instance.vals = {
            "Width": 200,
            "Height": 200
        }
        self.assertEqual(instance.annotations.count(), 2)
        annotations = Annotation.objects.filter(
            object_id = instance.pk
        )
        self.assertEqual(annotations.count(), 2)

    def test_annotate_invalid_type(self):
        instance = AnnotatedModel.objects.create(name="Test")
        with self.assertRaises(TypeError):
            instance.vals = {
                "Invalid Annotation Type": "Test",
            }
