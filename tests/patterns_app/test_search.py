from rest_framework.test import APITestCase
from wq.db.patterns.models import AnnotationType, Identifier
from wq.db.rest.models import get_ct
from .models import IdentifiedModel, AnnotatedModel, IdentifiedAnnotatedModel
from wq.db.contrib.search.util import search


class SearchTestCase(APITestCase):
    def setUp(self):
        # Create annotationtype
        AnnotationType.objects.create(name='Label')

        # 2 models with identifiers (one with two similar identifiers)
        IdentifiedModel.objects.find("Test")
        IdentifiedModel.objects.find("Test 2").identifiers.create(name="test2")

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
        self.assertEqual(len(search("Test", auto=False)), 7)

    def test_one_search(self):
        # Exact match should return one item
        self.assertEqual(len(search("Test 2", auto=True)), 1)

    def test_type_search(self):
        # Type filter should affect result
        ident_models = search("Test", False, "identifiedmodel")
        self.assertEqual(len(ident_models), 2)

        annot_models = search("Test", False, "annotatedmodel")
        self.assertEqual(len(annot_models), 3)

        # Duplicate match should be automatically removed in this case
        annot_models = search("Test", False, "identifiedannotatedmodel")
        self.assertEqual(len(annot_models), 1)

    def test_one_type_search(self):
        # Exact match but for wrong type should return zero items
        result = search("Test 2", True, "annotatedmodel")
        self.assertEqual(len(result), 0)
