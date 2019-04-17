from .base import APITestCase
from rest_framework import status
from tests.rest_app.models import (
    RootModel, OneToOneModel, ForeignKeyModel, ExtraModel, UserManagedModel,
    Parent, ItemType, SlugModel,
)
from django.contrib.auth.models import User


class RestTestCase(APITestCase):
    def setUp(self):
        instance = RootModel.objects.create(
            slug='instance',
            description="Test",
        )
        for cls in OneToOneModel, ForeignKeyModel, ExtraModel:
            cls.objects.create(
                root=instance,
            )
        self.user = User.objects.create(username="testuser")
        UserManagedModel.objects.create(id=1, user=self.user)
        parent = Parent.objects.create(name="Test", pk=1)
        parent.children.create(name="Test 1")
        parent.children.create(name="Test 2")
        parent2 = Parent.objects.create(name="Test 2", pk=2)
        parent2.children.create(name="Test 1")
        itype = ItemType.objects.create(name="Test", pk=1)
        itype.item_set.create(name="Test 1")
        itype.item_set.create(name="Test 2")
        SlugModel.objects.create(
            code="test",
            name="Test",
        )

    # Test url="" use case
    def test_rest_list_at_root(self):
        response = self.client.get("/.json")
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertTrue(len(response.data['list']) == 1)

    def test_rest_detail_at_root(self):
        response = self.client.get('/instance.json')
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertTrue(response.data['description'] == "Test")

    # Test nested models with foreign keys
    def test_rest_detail_nested_foreignkeys(self):
        response = self.client.get('/instance.json')

        # Include explicitly declared serializers for related fields
        self.assertIn("onetoonemodel", response.data)
        self.assertEqual(
            response.data["onetoonemodel"]["label"],
            "onetoonemodel for instance"
        )
        self.assertIn("extramodels", response.data)
        self.assertEqual(
            response.data["extramodels"][0]["label"],
            "extramodel for instance"
        )

        # Related fields without explicit serializers will not be included
        self.assertNotIn("extramodel_set", response.data)
        self.assertNotIn("foreignkeymodel_set", response.data)
        self.assertNotIn("foreignkeymodels", response.data)

    def test_rest_filter_by_parent(self):
        response = self.client.get('/parents/1/children.json')
        self.assertIn("list", response.data)
        self.assertEqual(len(response.data['list']), 2)

        response = self.client.get('/itemtypes/1/items.json')
        self.assertIn("list", response.data)
        self.assertEqual(len(response.data['list']), 2)

    def test_rest_target_to_children(self):
        response = self.client.get('/children-by-parents.json')
        self.assertIn("list", response.data)
        self.assertEqual(len(response.data['list']), 2)
        self.assertIn("target", response.data)
        self.assertEqual(response.data['target'], 'children')

    def test_rest_detail_user_serializer(self):
        response = self.client.get('/usermanagedmodels/1.json')
        self.assertIn('user', response.data)
        self.assertIn('label', response.data['user'])
        self.assertNotIn('password', response.data['user'])

    def test_rest_multi(self):
        lists = ['usermanagedmodels', 'items', 'children']
        response = self.client.get(
            "/multi.json?lists=" + ",".join(lists)
        )
        for listurl in lists:
            self.assertIn(listurl, response.data)
            self.assertIn("list", response.data[listurl])
            self.assertGreater(len(response.data[listurl]["list"]), 0)

    def test_rest_custom_lookup(self):
        response = self.client.get('/slugmodels/test.json')
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertEqual(response.data['id'], 'test')

    def test_rest_default_per_page(self):
        response = self.client.get('/parents.json')
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertEqual(response.data['per_page'], 50)

    def test_rest_custom_per_page(self):
        response = self.client.get('/children.json')
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertEqual(response.data['per_page'], 100)

    def test_rest_limit(self):
        response = self.client.get('/children.json?limit=10')
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertEqual(response.data['per_page'], 10)

    def test_rest_cache_all(self):
        for num in range(2, 101):
            ItemType.objects.create(
                pk=num,
                name='Type #%s' % num
            )

        tests = [
             (100, '/itemtypes.json'),
             (50, '/itemtypes/'),
             (50, '/itemtypes.json?page=1'),
        ]
        for expect_items, url in tests:
            response = self.client.get(url)
            self.assertTrue(
                status.is_success(response.status_code), response.data
            )
            self.assertEqual(
                len(response.data['list']), expect_items,
                "%s should return %s items" % (url, expect_items)
            )
            self.assertEqual(response.data['pages'], 2)
            self.assertEqual(response.data['per_page'], 50)
            self.assertEqual(response.data['count'], 100)

    def test_rest_cache_filter(self):
        other_user = User.objects.create(username='otheruser')
        UserManagedModel.objects.create(id=2, user=other_user)
        UserManagedModel.objects.create(id=3, user=other_user)

        for auth in False, True:
            if auth:
                self.client.force_authenticate(self.user)

            tests = [
                (3, 1 if auth else 0, '/usermanagedmodels.json'),
                (3, 3, '/usermanagedmodels/'),
                (3, 3, '/usermanagedmodels.json?page=1'),
                (1, 1, '/usermanagedmodels.json?user_id=%s' % self.user.pk),
                (2, 2, '/usermanagedmodels.json?user_id=%s' % other_user.pk),
            ]
            for expect_count, expect_items, url in tests:
                response = self.client.get(url)
                self.assertTrue(
                    status.is_success(response.status_code), response.data
                )
                self.assertEqual(
                    len(response.data['list']), expect_items,
                    "%s should return %s items for %s" % (
                        url, expect_items,
                        "authed user" if auth else "anonymous user"
                    )
                )
                self.assertEqual(response.data['pages'], 1)
                self.assertEqual(response.data['per_page'], 50)
                self.assertEqual(response.data['count'], expect_count)

    def test_rest_cache_none(self):
        tests = [
            (0, '/items.json'),
            (2, '/items/'),
            (2, '/items.json?page=1'),
        ]
        for expect_items, url in tests:
            response = self.client.get(url)
            self.assertTrue(
                status.is_success(response.status_code), response.data
            )
            self.assertEqual(
                len(response.data['list']), expect_items,
                "%s should return %s items" % (url, expect_items)
            )
            self.assertEqual(response.data['pages'], 1)
            self.assertEqual(response.data['per_page'], 50)
            self.assertEqual(response.data['count'], 2)

    def test_rest_list_head(self):
        response = self.client.head('/')
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )

    def test_rest_simpleviewset_head(self):
        response = self.client.head('/login')
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )

    def test_rest_options(self):
        response = self.client.options('/')
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
