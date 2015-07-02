from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from tests.patterns_app.models import LocatedModel
from wq.db.patterns.models import Location
import json


class LocateRestTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', is_superuser=True)
        self.instance = LocatedModel.objects.create(name="Test 1")
        self.instance.locations.create(geometry='POINT(-91 46)')
        self.instance.locations.create(geometry='POINT(-96 45)')
        self.client.force_authenticate(user=self.user)

    def test_locate_post(self):
        """
        POSTing to a locatedmodel's viewset with a GeoJSON FeatureCollection in
        the "locations" field should result in Location objects being created.
        """
        form = {
            'name': 'Test 2',
            'locations': json.dumps({
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-95, 45]
                        }
                    },
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-94, 49]
                        }
                    }
                ]
            })
        }

        # Test for expected response
        response = self.client.post('/locatedmodels.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data['name'], "Test 2")
        self.assertIn("locations", response.data)
        self.assertEqual(len(response.data["locations"]), 2)

        # Double-check ORM models & geometry attributes
        locs = Location.objects.filter(object_id=response.data['id'])
        self.assertEqual(len(locs), 2)

        geom = locs[0].geometry
        self.assertEqual(geom.srid, 4326)
        self.assertEqual(geom.x, -95)
        self.assertEqual(geom.y, 45)

    def test_locate_put(self):
        """
        PUTting to a locatedmodel's viewset with a GeoJSON FeatureCollection in
        the "locations" field should result in existing Location objects being
        updated, or (if necessary) new Location objects being created.
        """

        existing = self.instance.locations.all()
        eid1 = existing[0].id
        eid2 = existing[1].id

        form = {
            'name': 'Test 1 - Updated',
            'locations': json.dumps({
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "id": eid1,
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-92, 47]
                        }
                    },
                    {
                        "type": "Feature",
                        "id": eid2,
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-93, 48]
                        }
                    },
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-94, 49]
                        }
                    }
                ]
            })
        }

        # Test for expected response
        response = self.client.put(
            '/locatedmodels/%s.json' % self.instance.pk,
            form
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.instance = LocatedModel.objects.get(pk=self.instance.pk)
        self.assertEqual(self.instance.name, "Test 1 - Updated")
        self.assertIn("locations", response.data)
        self.assertEqual(len(response.data["locations"]), 3)

        # Double-check ORM models & geometry attributes
        locs = self.instance.locations.all()
        geom = locs.get(id=eid1).geometry
        self.assertEqual(geom.srid, 4326)
        self.assertEqual(geom.x, -92)
        self.assertEqual(geom.y, 47)

        newlocs = locs.exclude(id__in=[eid1, eid2]).all()
        self.assertEqual(len(newlocs), 1)

    def test_locate_list_geojson(self):
        pk = self.instance.pk
        loc1 = self.instance.locations.all()[0]
        loc2 = self.instance.locations.all()[1]
        expected = {
            'type': 'FeatureCollection',
            'features': [{
                'id': pk,
                'type': 'Feature',
                'properties': {
                    'name': 'Test 1',
                    'label': 'Test 1',
                },
                'geometry': {
                    "type": "GeometryCollection",
                    "geometries": [
                        {
                            "type": "Point",
                            "coordinates": [loc1.geometry.x, loc1.geometry.y],
                            "@index": 0,
                        },
                        {
                            "type": "Point",
                            "coordinates": [loc2.geometry.x, loc2.geometry.y],
                            "@index": 1,
                        }
                    ]
                }
            }],

            # NOTE: These (and @index) are wq.db-specific and not part of the
            # GeoJSON spec.
            'count': 1,
            'multiple': False,
            'page': 1,
            'pages': 1,
            'per_page': 50,
            'previous': None,
            'next': None,
        }

        # Test for expected response
        response = self.client.get('/locatedmodels.geojson')
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(expected, data)

    def test_locate_detail_geojson(self):
        pk = self.instance.pk
        loc1 = self.instance.locations.all()[0]
        loc2 = self.instance.locations.all()[1]
        expected = {
            'id': pk,
            'type': 'Feature',
            'properties': {
                'name': 'Test 1',
                'label': 'Test 1',
            },
            'geometry': {
                "type": "GeometryCollection",
                "geometries": [
                    {
                        "type": "Point",
                        "coordinates": [loc1.geometry.x, loc1.geometry.y],
                        "@index": 0,
                    },
                    {
                        "type": "Point",
                        "coordinates": [loc2.geometry.x, loc2.geometry.y],
                        "@index": 1,
                    }
                ]
            }
        }

        # NOTE: @index is wq.db-specific and not part of the GeoJSON spec

        # Test for expected response
        response = self.client.get('/locatedmodels/%s.geojson' % pk)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(expected, data)

    def test_locate_edit_geojson(self):
        pk = self.instance.pk
        loc1 = self.instance.locations.all()[0]
        loc2 = self.instance.locations.all()[1]
        expected = {
            'type': 'FeatureCollection',
            'features': [{
                "id": loc1.pk,
                "type": "Feature",
                "properties": {
                    "@index": 0,
                    "accuracy": None,
                    "is_primary": False,
                    "label": "Location %s - Test 1" % loc1.pk,
                    "name": None,
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [loc1.geometry.x, loc1.geometry.y],
                },
            }, {
                "id": loc2.pk,
                "type": "Feature",
                "properties": {
                    "@index": 1,
                    "accuracy": None,
                    "is_primary": False,
                    "label": "Location %s - Test 1" % loc2.pk,
                    "name": None,
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [loc2.geometry.x, loc2.geometry.y],
                }
            }],

            # NOTE: id/properties on FeatureCollection not part of GeoJSON spec
            'id': pk,
            'properties': {
                'edit': True,
                'name': 'Test 1',
                'label': 'Test 1',
            }
        }

        # Test for expected response
        response = self.client.get('/locatedmodels/%s/edit.geojson' % pk)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(expected, data)
