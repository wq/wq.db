import unittest
from .base import APITestCase
from django.conf import settings


class VectorTileTestCase(APITestCase):
    @unittest.skipIf(settings.VARIANT == "postgis", "postgis supports tiles")
    def test_no_tiles(self):
        tile = self.client.get("/tiles/0/0/0.pbf")
        self.assertEqual(
            tile.content.decode(),
            "Tile server not supported with this database engine.",
        )

    @unittest.skipUnless(settings.VARIANT == "postgis", "requires postgis")
    def test_tiles(self):
        from .gis_app.models import PointModel

        empty_tile = self.client.get("/tiles/0/0/0.pbf").content
        self.assertEqual(b"", empty_tile)

        PointModel.objects.create(pk=1, geometry="POINT(34 -84)")
        single_point = self.client.get("/tiles/0/0/0.pbf").content
        self.assertEqual(
            single_point,
            b'\x1a\x1e\n\npointmodel\x12\x0b\x08\x01\x18\x01"\x05\t\x86&\x84>(\x80 x\x02',
        )
