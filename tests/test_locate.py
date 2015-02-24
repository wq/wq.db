from wq.db.rest.models import get_ct
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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
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
        updated.
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
                    }
                ]
            })
        }

        # Test for expected response
        response = self.client.put(
            '/locatedmodels/%s.json' % self.instance.pk,
            form
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.instance = LocatedModel.objects.get(pk=self.instance.pk)
        self.assertEqual(self.instance.name, "Test 1 - Updated")
        self.assertIn("locations", response.data)

        # Double-check ORM models & geometry attributes
        locs = self.instance.locations.all()
        geom = locs.get(id=eid1).geometry
        self.assertEqual(geom.srid, 4326)
        self.assertEqual(geom.x, -92)
        self.assertEqual(geom.y, 47)
