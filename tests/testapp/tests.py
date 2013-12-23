from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import RootModel, AnnotatedModel
from wq.db.patterns.models import AnnotationType, Annotation
from wq.db.contrib.vera.models import (
    Event, Report, ReportStatus, Site, Parameter
)
import json
import datetime


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
            object_id=instance.pk
        )
        self.assertEqual(annotations.count(), 2)

    def test_annotate_invalid_type(self):
        instance = AnnotatedModel.objects.create(name="Test")
        with self.assertRaises(TypeError):
            instance.vals = {
                "Invalid Annotation Type": "Test",
            }


class VeraTestCase(APITestCase):
    def setUp(self):
        self.site = Site.objects.find(45, -95)
        self.user = User.objects.create(username='testuser')
        self.valid = ReportStatus.objects.create(is_valid=True)
        self.invalid = ReportStatus.objects.create(is_valid=False)

        # Numeric parameters
        param1 = Parameter.objects.find('Temperature')
        param1.is_numeric = True
        param1.units = 'C'
        param1.save()

        param2 = Parameter.objects.find('Wind Speed')
        param2.is_numeric = True
        param2.units = 'm/s'
        param2.save()

        # Text parameters
        Parameter.objects.find('Notes')
        Parameter.objects.find('Rain')

    def test_vera_simple(self):
        # Single report
        event_key = [45, -95, '2014-01-01']
        Report.objects.create_report(
            event_key,
            {
                'Temperature': 5,
                'Notes': 'Test Observation'
            },
            user=self.user,
            status=self.valid,
        )
        # Test that event exists and has correct values
        instance = Event.objects.get_by_natural_key(*event_key)
        self.assertEqual(instance.date, datetime.date(2014, 1, 1))
        self.assertEqual(instance.site.pk, self.site.pk)
        self.assertEqual(instance.vals['temperature'], 5)
        self.assertEqual(instance.vals['notes'], 'Test Observation')

    def test_vera_report_merge(self):
        event_key = [45, -95, '2014-01-02']

        # Three reports for the same event

        # Initial valid report
        Report.objects.create_report(
            event_key,
            {
                'Temperature': 5,
                'Notes': 'Test Observation'
            },
            user=self.user,
            status=self.valid,
        )

        # Subsequent valid report, should override above
        Report.objects.create_report(
            event_key,
            {
                'Temperature': 5.3,
                'Wind Speed': 10,
            },
            user=self.user,
            status=self.valid,
        )

        # Subsequent invalid report, should not override above (or appear
        #  in event at all)
        Report.objects.create_report(
            event_key,
            {
                'Wind Speed': 15,
                'Rain': 'N'
            },
            user=self.user,
            status=self.invalid,
        )

        # Test that each parameter has the latest valid value
        instance = Event.objects.get_by_natural_key(*event_key)
        self.assertEqual(instance.vals['temperature'], 5.3)
        self.assertEqual(instance.vals['notes'], 'Test Observation')
        self.assertEqual(instance.vals['wind-speed'], 10)
        self.assertNotIn('rain', instance.vals)

    def test_vera_invalid_param(self):
        event_key = [45, -95, '2014-01-01']
        values = {
            'Invalid Parameter': 5,
            'Notes': 'Test Observation'
        }
        with self.assertRaises(TypeError):
            Report.objects.create_report(
                event_key,
                values,
                user=self.user
            )
