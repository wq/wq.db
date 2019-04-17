import unittest
from .base import APITestCase
from rest_framework import status
import json
from tests.rest_app.models import SlugModel
from tests.gis_app.models import GeometryModel
from django.contrib.auth.models import User
from django.conf import settings


class RestPostTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser", is_superuser=True)
        self.client.force_authenticate(self.user)

    @unittest.skipUnless(settings.WITH_GIS, "requires GIS")
    def test_rest_geometry_post_geojson(self):
        """
        Posting GeoJSON to a model with a geometry field should work.
        """
        form = {
            'name': "Geometry Test 1",
            'geometry': json.dumps({
                "type": "Point",
                "coordinates": [-90, 44]
            })
        }

        # Test for expected response
        response = self.client.post('/geometrymodels.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )

        # Double-check ORM model & geometry attribute
        obj = GeometryModel.objects.get(id=response.data['id'])
        geom = obj.geometry
        self.assertEqual(geom.srid, 4326)
        self.assertEqual(geom.x, -90)
        self.assertEqual(geom.y, 44)

    @unittest.skipUnless(settings.WITH_GIS, "requires GIS")
    def test_rest_geometry_post_wkt(self):
        """
        Posting WKT to a model with a geometry field should work.
        """
        form = {
            'name': "Geometry Test 2",
            'geometry': "POINT(%s %s)" % (-97, 50)
        }

        # Test for expected response
        response = self.client.post('/geometrymodels.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )

        # Double-check ORM model & geometry attribute
        obj = GeometryModel.objects.get(id=response.data['id'])
        geom = obj.geometry
        self.assertEqual(geom.srid, 4326)
        self.assertEqual(geom.x, -97)
        self.assertEqual(geom.y, 50)

    def test_rest_date_label_post(self):
        """
        Posting to a model with a date should return a label and an ISO date
        """
        form = {
            'name': "Test Date",
            'date': '2015-06-01 12:00:00Z',
        }
        response = self.client.post("/datemodels.json", form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertIn('date_label', response.data)
        self.assertEqual(response.data['date_label'], "2015-06-01 07:00 AM")
        self.assertIn('date', response.data)
        self.assertEqual(response.data['date'], "2015-06-01T07:00:00-05:00")

    def test_rest_empty_date_post(self):
        """
        Allow posting an empty date if the field allows nulls
        """
        form = {
            'name': "Test Date",
            'date': '2015-06-01 12:00:00Z',
            'empty_date': '',
        }
        response = self.client.post("/datemodels.json", form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )

    def test_rest_empty_string(self):
        def check_result(form, expected_output):
            response = self.client.post("/charfieldmodels.json", form)
            if not expected_output:
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                    response.data
                )
                return

            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, response.data
            )
            for field, value in expected_output.items():
                if value is None:
                    self.assertIsNone(response.data[field])
                else:
                    self.assertEqual(response.data[field], value)

        # No fields submitted
        check_result({}, False)

        # Required field submitted but left blank
        check_result({'required_field': ''}, False)

        # Required field submitted
        check_result({
            'required_field': 'test',
        }, {
            'required_field': 'test',
            'nullable_field': None,
            'blankable_field': '',
            'nullableblankable_field': None,
        })

        # All fields submitted but left blank
        check_result({
            'required_field': 'test',
            'nullable_field': '',
            'blankable_field': '',
            'nullableblankable_field': '',
        }, {
            'required_field': 'test',
            'nullable_field': None,
            'blankable_field': '',
            'nullableblankable_field': '',
        })

    def test_rest_custom_lookup_fk(self):
        SlugModel.objects.create(
            code='test1',
            name='Test #1',
        )
        response = self.client.post('/slugrefparents.json', {
            'ref_id': 'test1',
            'name': "Test FK",
        })
        self.assertTrue(status.is_success(response.status_code), response.data)
        rid = response.data.get('id')
        self.assertEqual(response.data, {
            'id': rid,
            'label': 'Test FK (Test #1)',
            'name': 'Test FK',
            'ref_id': 'test1',
            'ref_label': 'Test #1',
        })

        response = self.client.post('/slugrefparents.json', {
            'ref_id': 'test_invalid',
            'name': "Test FK",
        })
        self.assertTrue(
            status.is_client_error(response.status_code), response.data
        )
        self.assertEqual(response.data, {
            'ref_id': ['Object with code=test_invalid does not exist.']
        })

    def test_rest_list_exclude_post(self):
        # Create
        response = self.client.post('/expensivemodels.json', {
            "name": "Test",
            "expensive": "SOME_DATA",
        })
        item = response.data
        item_url = '/expensivemodels/{pk}.json'.format(pk=item['id'])
        self.assertEqual(item['name'], "Test")
        self.assertEqual(item['expensive'], "SOME_DATA")

        # List view
        response = self.client.get('/expensivemodels.json')
        item = response.data['list'][0]
        self.assertEqual(item['name'], "Test")
        self.assertNotIn('expensive', item)
        self.assertNotIn('more_expensive', item)

        # Detail view
        response = self.client.get(item_url)
        item = response.data
        self.assertEqual(item['name'], "Test")
        self.assertEqual(item['expensive'], "SOME_DATA")

        # Update
        response = self.client.put(item_url, {
            "name": "Test 2",
            "expensive": "SOME_OTHER_DATA",
        })
        item = response.data
        self.assertEqual(item['name'], "Test 2")
        self.assertEqual(item['expensive'], "SOME_OTHER_DATA")
