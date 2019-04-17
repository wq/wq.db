from .base import APITestCase
from rest_framework import status
from tests.rest_app.models import ItemType, DateModel, ChoiceModel
from tests.rest_app.serializers import (
    ChoiceLabelSerializer, DateLabelSerializer, ItemLabelSerializer,
)


class LabelTestCase(APITestCase):
    def setUp(self):
        itype = ItemType.objects.create(name="Test", pk=1)
        itype.item_set.create(name="Test 1")
        DateModel.objects.create(
            pk=1,
            name="Test",
            date="2015-01-01 12:00Z",
        )
        ChoiceModel.objects.create(
            pk=1,
            name="Test",
            choice="two",
        )

    def test_rest_date_label(self):
        response = self.client.get("/datemodels/1.json")
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertIn('date_label', response.data)
        self.assertEqual(response.data['date_label'], "2015-01-01 06:00 AM")

    def test_rest_choice_label(self):
        response = self.client.get("/choicemodels/1.json")
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertIn('choice_label', response.data)
        self.assertEqual(response.data['choice_label'], "Choice Two")

    def test_rest_boolean_label(self):
        response = self.client.get("/itemtypes/1.json")
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertIn('active_label', response.data)
        self.assertEqual(response.data['active_label'], "Yes")

    def test_custom_date_label(self):
        from wq.db.rest import router

        # Default label
        item = DateModel.objects.get(pk=1)
        obj = router.serialize(item)
        self.assertEqual(obj['date_label'], '2015-01-01 06:00 AM')

        # Custom label
        obj = DateLabelSerializer(item).data
        self.assertEqual(obj['date_label'], 'January 1, 2015')

    def test_custom_choice_label(self):
        from wq.db.rest import router

        # Default label
        item = ChoiceModel.objects.get(pk=1)
        obj = router.serialize(item)
        self.assertEqual(obj['choice_label'], 'Choice Two')

        # Custom label
        obj = ChoiceLabelSerializer(item).data
        self.assertEqual(obj['choice_label'], 'TWO')

    def test_custom_fk_label(self):
        from wq.db.rest import router

        # Default labels
        item = ItemType.objects.get(pk=1).item_set.get(name='Test 1')
        obj = router.serialize(item)
        self.assertEqual(obj['type_id'], 1)
        self.assertEqual(obj['type_label'], 'Test')
        self.assertEqual(obj['label'], 'Test 1')

        # Custom labels
        obj = ItemLabelSerializer(item).data
        self.assertEqual(obj['type_id'], 'id-1')
        self.assertEqual(obj['type_label'], 'TEST')
        self.assertEqual(obj['label'], 'Test: Test 1')
