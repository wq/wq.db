from rest_framework.test import APITestCase
from rest_framework import status
from wq.db.patterns.models import AnnotationType, Authority
from tests.patterns_app.models import (
    IdentifiedModel, AnnotatedModel, IdentifiedAnnotatedModel
)
from wq.db.contrib.search.util import search


class BaseSearchTestCase(APITestCase):
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


class SearchTestCase(BaseSearchTestCase):
    def test_search_all(self):
        # "Test" should match all 6 items..
        # but there will be one duplicate (Test 6) due to filter limitations
        self.assertResults(7, "Test", auto=False)

    def test_search_one(self):
        # Exact match should return one item
        self.assertResults(1, "Test 2", auto=True)

    def test_search_type(self):
        # Type filter should affect result
        self.assertResults(2, "Test", False, "identifiedmodel")
        self.assertResults(3, "Test", False, "annotatedmodel")

        # Duplicate match should be automatically removed in this case
        self.assertResults(1, "Test", False, "identifiedannotatedmodel")

    def test_search_one_type(self):
        # Exact match but for wrong type should return zero items
        self.assertResults(0, "Test 2", True, "annotatedmodel")

    def test_search_authority(self):
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


class SearchRestTestCase(BaseSearchTestCase):
    def test_search_rest_all(self):
        # "Test" should match all 6 items..
        # but there will be one duplicate (Test 6) due to filter limitations
        self.assertResults(7, "Test", auto=False)

    def test_search_rest_one(self):
        # Exact match with auto should redirect
        result = self.run_search("Test 2", auto=True)
        self.assertEqual(result.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            result['Location'].replace('http://testserver', ''),
            '/identifiedmodels/test-2'
        )

    def test_search_rest_disambiguate(self):
        # Disambiguate view - shortcut for exact match with auto, should
        # redirect (normally this view would be mapped to the top level URL
        # after any other urls)
        result = self.client.get('/search/test-2')
        self.assertEqual(result.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            result['Location'].replace('http://testserver', ''),
            '/identifiedmodels/test-2'
        )

    def test_search_rest_disambiguate_fail(self):
        # If multiple results returned, list all potential matches instead of
        # redirecting.
        result = self.client.get('/search/Test')
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        annotmodels = {}
        for i, model in enumerate(AnnotatedModel.objects.all()):
            annotmodels['pk%s' % (i + 1)] = model.pk
        self.assertHTMLEqual(
            result.content.decode('utf-8'),
            """
            <ul>
              <li><a href="/identifiedannotatedmodels/test-6">Test 6</a></li>
              <li><a href="/identifiedmodels/test">Test</a></li>
              <li><a href="/identifiedmodels/test-2">Test 2</a></li>
              <li><a href="/annotatedmodels/{pk1}">Test 3</a></li>
              <li><a href="/annotatedmodels/{pk2}">Test 4</a></li>
              <li><a href="/annotatedmodels/{pk3}">Test 5</a></li>
              <li><a href="/identifiedannotatedmodels/test-6">Test 6</a></li>
            </ul>
            """.format(**annotmodels)
        )

    def test_search_rest_type(self):
        # Type filter should affect result
        self.assertResults(2, "Test", False, "identifiedmodel")
        self.assertResults(3, "Test", False, "annotatedmodel")

        # Duplicate match should be automatically removed in this case
        self.assertResults(1, "Test", False, "identifiedannotatedmodel")

    def test_search_rest_one_type(self):
        # Exact match but for wrong type should return zero items
        self.assertResults(0, "Test 2", True, "annotatedmodel")

    def test_search_rest_authority(self):
        # Authority filter should affect result
        self.assertResults(1, "Test", False, "identifiedmodel", self.auth.id)

    def run_search(self, query, auto, content_type=None, authority_id=None):
        params = {
            'q': query,
        }
        if auto:
            params['auto'] = True
        if content_type:
            params['type'] = content_type
        if authority_id:
            params['authority_id'] = authority_id

        return self.client.get('/search/search.json', params)

    def assertResults(self, expected_count, *args, **kwargs):
        result = self.run_search(*args, **kwargs)
        result_count = len(result.data['list'])
        self.assertEqual(result_count, expected_count)
