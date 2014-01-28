from rest_framework.test import APITestCase
import swapper


class SwapTestCase(APITestCase):
    def test_swap(self):
        self.assertEqual(swapper.is_swapped("vera", "Site"), "swap_app.Site")
        Site = swapper.load_model("vera", "Site")
        self.assertTrue(hasattr(Site, "identifiers"))
        site = Site.objects.find("Site 1")
        self.assertEqual(unicode(site), "Site 1")
