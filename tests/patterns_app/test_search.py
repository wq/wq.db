from rest_framework.test import APITestCase
from wq.db.patterns.models import AnnotationType, Identifier, Authority
from wq.db.rest.models import get_ct
from .models import IdentifiedModel, AnnotatedModel, IdentifiedAnnotatedModel
from wq.db.contrib.search.util import search


class SearchTestCase(APITestCase):
    def setUp(self):
        # Create annotationtype & authority
        AnnotationType.objects.create(name='Label')
        self.auth = Authority.objects.create(name='Identifying Authority')

        # 2 models with identifiers (one with two similar identifiers)
        IdentifiedModel.objects.find("Test")
        IdentifiedModel.objects.find("Test 2").identifiers.create(
            name="test2",
            authority=self.auth,
        )

        # 3 models with annotations
        AnnotatedModel.objects.create(name="Test 3").vals = {'Label': 'Test 3'}
        AnnotatedModel.objects.create(name="Test 4").vals = {'Label': 'Test 4'}
        AnnotatedModel.objects.create(name="Test 5").vals = {'Label': 'Test 5'}

        # 1 model with a matching identifier and annotation
        IdentifiedAnnotatedModel.objects.find("Test 6").vals = {
            'Label': 'Test 6'
        }

    def test_all_search(self):
        # "Test" should match all 6 items..
        # but there will be one duplicate (Test 6) due to filter limitations
        self.assertResults(7, "Test", auto=False)

    def test_one_search(self):
        # Exact match should return one item
        self.assertResults(1, "Test 2", auto=True)

    def test_type_search(self):
        # Type filter should affect result
        self.assertResults(2, "Test", False, "identifiedmodel")
        self.assertResults(3, "Test", False, "annotatedmodel")

        # Duplicate match should be automatically removed in this case
        self.assertResults(1, "Test", False, "identifiedannotatedmodel")

    def test_one_type_search(self):
        # Exact match but for wrong type should return zero items
        self.assertResults(0, "Test 2", True, "annotatedmodel")

    def test_auth_search(self):
        # Authority filter should affect result
        self.assertResults(1, "Test", False, "identifiedmodel", self.auth.id)

    def run_search(self, *args, **kwargs):
        result = search(*args, **kwargs)
        len1 = len(result)
        len2 = len(list(result))
        self.assertEqual(len1, len2)
        return len1

    def assertResults(self, expected_count, *args, **kwargs):
        result_count = self.run_search(*args, **kwargs)
        self.assertEqual(result_count, expected_count)
