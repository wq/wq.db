import unittest
from .base import APITestCase
from rest_framework import status
from django.conf import settings
from .gis_app.models import GeometryModel, PointModel
from django.contrib.auth.models import User
import json


class GISTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser", is_superuser=True)
        self.client.force_authenticate(self.user)

    @unittest.skipUnless(settings.WITH_GIS, "requires GIS")
    def test_rest_geometry_post_geojson(self):
        """
        Posting GeoJSON to a model with a geometry field should work.
        """
        form = {
            "name": "Geometry Test 1",
            "geometry": json.dumps(
                {"type": "Point", "coordinates": [-90, 44]}
            ),
        }

        # Test for expected response
        response = self.client.post("/geometrymodels.json", form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )

        # Double-check ORM model & geometry attribute
        obj = GeometryModel.objects.get(id=response.data["id"])
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
            "name": "Geometry Test 2",
            "geometry": "POINT(%s %s)" % (-97, 50),
        }

        # Test for expected response
        response = self.client.post("/geometrymodels.json", form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )

        # Double-check ORM model & geometry attribute
        obj = GeometryModel.objects.get(id=response.data["id"])
        geom = obj.geometry
        self.assertEqual(geom.srid, 4326)
        self.assertEqual(geom.x, -97)
        self.assertEqual(geom.y, 50)

    @unittest.skipIf(settings.VARIANT == "postgis", "postgis supports tiles")
    def test_no_tiles(self):
        tile = self.client.get("/tiles/0/0/0.pbf")
        self.assertEqual(
            tile.content.decode(),
            "Tile server not supported with this database engine.",
        )

    @unittest.skipUnless(settings.VARIANT == "postgis", "requires postgis")
    def test_tiles(self):
        empty_tile = self.client.get("/tiles/0/0/0.pbf").content
        self.assertEqual(b"", empty_tile)

        PointModel.objects.create(pk=1, geometry="POINT(34 -84)")
        single_point = self.client.get("/tiles/0/0/0.pbf").content
        self.assertEqual(
            single_point,
            b'\x1a\x1e\n\npointmodel\x12\x0b\x08\x01\x18\x01"\x05\t\x86&\x84>(\x80 x\x02',
        )

    @unittest.skipUnless(settings.WITH_GIS, "requires GIS")
    def test_defer_geometry(self):
        PointModel.objects.create(pk=1, geometry="POINT(34 -84)")
        points_json = self.client.get("/pointmodels.json").data["list"]
        self.assertEqual(
            points_json,
            [
                {
                    "id": 1,
                    "name": "",
                    "label": "",
                }
            ],
        )
        points_geojson = self.client.get("/pointmodels.geojson").data[
            "features"
        ]
        self.assertEqual(
            points_geojson,
            [
                {
                    "id": 1,
                    "type": "Feature",
                    "properties": {
                        "name": "",
                        "label": "",
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [34, -84],
                    },
                }
            ],
        )
