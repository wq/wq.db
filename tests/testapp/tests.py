from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import RootModel, AnnotatedModel
from wq.db.patterns.models import AnnotationType, Annotation
from wq.db.contrib.vera.models import (
    Event, Report, ReportStatus, Site, Parameter, EventResult
)
from wq.db.rest.models import get_ct
import json
import datetime


def value_by_type(attachments):
    return {
        a['type_id']: a['value'] for a in attachments
    }


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


class AnnotateRestTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', is_superuser=True)
        ct = get_ct(AnnotatedModel)
        self.width = AnnotationType.objects.create(
            name="Width",
            contenttype=ct
        )
        self.height = AnnotationType.objects.create(
            name="Height",
            contenttype=ct
        )
        self.instance = AnnotatedModel.objects.create(name="Test 1")
        self.instance.vals = {
            'Width': 200,
            'Height': 200
        }
        self.client.force_authenticate(user=self.user)

    def test_annotate_post(self):
        form = {
            'name': 'Test 2'
        }
        form['annotation-%s-value' % self.width.pk] = 350
        form['annotation-%s-value' % self.height.pk] = 400
        response = self.client.post('/annotatedmodels.json', form)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Test 2")
        self.assertIn("annotations", response.data)
        self.assertEqual(len(response.data["annotations"]), 2)
        values = value_by_type(response.data['annotations'])
        self.assertEqual(values[self.width.pk], '350')
        self.assertEqual(values[self.height.pk], '400')

    def test_annotate_put(self):
        form = {
            'name': 'Test 1 - Updated'
        }
        for aname in 'width', 'height':
            atype = getattr(self, aname)
            prefix = 'annotation-%s-' % atype.pk
            form[prefix + 'id'] = self.instance.annotations.get(type=atype).pk
            form[prefix + 'value'] = 600

        response = self.client.put(
            '/annotatedmodels/%s.json' % self.instance.pk,
            form
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.instance = AnnotatedModel.objects.get(pk=self.instance.pk)
        self.assertEqual(self.instance.name, "Test 1 - Updated")
        self.assertIn("annotations", response.data)
        self.assertEqual(len(response.data["annotations"]), 2)
        values = value_by_type(response.data['annotations'])
        for aname in 'width', 'height':
            atype = getattr(self, aname)
            self.assertEqual(values[atype.pk], '600')
            self.assertEqual(
                self.instance.annotations.get(type=atype).value,
                '600'
            )


class VeraTestCase(APITestCase):
    def setUp(self):
        self.site = Site.objects.find(45, -95)
        self.user = User.objects.create(username='testuser')
        self.valid = ReportStatus.objects.create(is_valid=True, slug='valid')
        self.invalid = ReportStatus.objects.create(slug='invalid')

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

    def test_vera_merge_eventresult(self):
        event_key = [45, -95, '2014-01-10']

        # Two reports for the same event, EventResult should contain
        # two rows for the event (which should correspond to event.results)
        Report.objects.create_report(
            event_key,
            {
                'Temperature': 6,
                'Notes': 'Test Observation 3'
            },
            user=self.user,
            status=self.valid,
        )

        # Subsequent valid report, should override above
        Report.objects.create_report(
            event_key,
            {
                'Temperature': 5.3,
            },
            user=self.user,
            status=self.valid
        )
        event = Event.objects.get_by_natural_key(*event_key)
        ers = EventResult.objects.filter(event=event)
        self.assertEqual(ers.count(), 2)
        self.assertEqual(
            ers.get(result_type__name='Temperature').result_value_numeric,
            5.3
        )
        self.assertEqual(
            ers.get(result_type__name='Notes').result_value_text,
            'Test Observation 3'
        )


class VeraRestTestCase(APITestCase):
    def setUp(self):
        self.site = Site.objects.find(45, -95)
        self.user = User.objects.create(username='testuser', is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.valid = ReportStatus.objects.create(is_valid=True, slug='valid')

        param1 = Parameter.objects.find('Temperature')
        param1.is_numeric = True
        param1.units = 'C'
        param1.save()

        Parameter.objects.find('Notes')

    def test_vera_post(self):
        form = {
            'site__latitude': 45,
            'site__longitude': -95.5,
            'date': '2014-01-03',
            'result-temperature-value': 6,
            'result-notes-value': 'Test Observation',
        }
        response = self.client.post('/reports.json', form)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data['event_label'],
            "45.0, -95.5 on 2014-01-03"
        )
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)
        values = value_by_type(response.data['results'])
        self.assertEqual(values['temperature'], 6.0)
        self.assertEqual(values['notes'], 'Test Observation')

    def test_vera_post_merge(self):
        # Submit first report (but don't validate it)
        # Event should exist but have no result values
        form1 = {
            'site__latitude': 45,
            'site__longitude': -95.5,
            'date': '2014-01-04',
            'result-temperature-value': 6,
            'result-notes-value': 'Test Observation 2',
        }
        response1 = self.client.post('/reports.json', form1)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        event_id = response1.data['event_id']
        event = self.client.get('/events/%s.json' % event_id).data
        self.assertEqual(len(event['results']), 0)

        # Submit second report and validate it
        # Event should contain a single result value
        form2 = {
            'site__latitude': 45,
            'site__longitude': -95.5,
            'date': '2014-01-04',
            'result-temperature-value': 7,
            'status': 'valid'
        }
        response2 = self.client.post('/reports.json', form2)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response1.data['event_id'], event_id)
        event = self.client.get('/events/%s.json' % event_id).data
        self.assertEqual(len(event['results']), 1)

        # Validate original report
        # Event should now have the temperature value from the second report
        # and the notes from the first.
        self.client.patch(
            '/reports/%s.json' % response1.data['id'],
            {'status': 'valid'}
        )
        event = self.client.get('/events/%s.json' % event_id).data
        self.assertEqual(len(event['results']), 2)
        values = value_by_type(event['results'])
        self.assertEqual(values['temperature'], 7)
        self.assertEqual(values['notes'], 'Test Observation 2')
