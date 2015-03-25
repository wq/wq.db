from wq.db.rest.models import get_ct
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from tests.patterns_app.models import RelatedModel, AnotherRelatedModel
from wq.db.patterns.models import RelationshipType, Relationship


class RelateBaseTestCase(APITestCase):
    def setUp(self):
        self.parent_ct = get_ct(RelatedModel)
        self.child_ct = get_ct(AnotherRelatedModel)

        self.reltype = RelationshipType.objects.create(
            name="Parent Of",
            inverse_name="Child Of",
            from_type=self.parent_ct,
            to_type=self.child_ct,
        )
        self.parent = RelatedModel.objects.create(name="Parent1")
        self.child = AnotherRelatedModel.objects.create(name="Child1")

        Relationship.objects.create(
            type=self.reltype,

            from_content_type=self.parent_ct,
            from_object_id=self.parent.pk,

            to_content_type=self.parent_ct,
            to_object_id=self.child.pk,
        )


class RelateTestCase(RelateBaseTestCase):
    def test_relate_forward(self):
        self.assertEqual(self.parent.relationships.count(), 1)
        self.assertEqual(self.parent.inverserelationships.count(), 0)
        rel = self.parent.relationships.all()[0]
        self.assertEqual(rel.left, self.parent)
        self.assertEqual(rel.right, self.child)
        self.assertEqual(str(rel), "Parent1 Parent Of Child1")
        self.assertEqual(str(rel.reltype), "Parent Of")
        self.assertEqual(rel.reltype.pk, self.reltype.pk)

    def test_relate_inverse(self):
        self.assertEqual(self.child.inverserelationships.count(), 1)
        self.assertEqual(self.child.relationships.count(), 0)
        invrel = self.child.inverserelationships.all()[0]
        self.assertEqual(invrel.left, self.child)
        self.assertEqual(invrel.right, self.parent)
        self.assertEqual(str(invrel), "Child1 Child Of Parent1")
        self.assertEqual(str(invrel.reltype), "Child Of")
        self.assertEqual(invrel.reltype.pk, self.reltype.pk)

    def test_relate_create(self):
        child2 = AnotherRelatedModel.objects.create(name="Child2")
        rel = self.child.create_relationship(
            child2,
            name="Sibling Of",
            inverse_name="Sibling Of",
        )
        self.assertEqual(rel.reltype.from_type.pk, self.child_ct.pk)
        self.assertEqual(rel.reltype.to_type.pk, self.child_ct.pk)
        self.assertEqual(str(rel), "Child1 Sibling Of Child2")
        self.assertEqual(str(rel.reltype), "Sibling Of")

        invrel = child2.inverserelationships.all()[0]
        self.assertEqual(str(invrel), "Child2 Sibling Of Child1")
        self.assertEqual(str(invrel.reltype), "Sibling Of")


class RelateRestTestCase(RelateBaseTestCase):
    def setUp(self):
        super(RelateRestTestCase, self).setUp()
        self.user = User.objects.create(username='testuser', is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_relate_get_forward(self):
        response = self.client.get(
            '/relatedmodels/%s.json' % self.parent.pk
        )
        self.assertIn('relationships', response.data)
        self.assertEqual(len(response.data['relationships']), 1)
        rel = response.data['relationships'][0]
        self.assertEqual(rel['type_label'], 'Parent Of')
        self.assertEqual(rel['item_id'], self.child.pk)
        self.assertEqual(rel['item_label'], str(self.child))
        self.assertEqual(rel['item_page'], 'anotherrelatedmodel')
        self.assertEqual(
            rel['item_url'],
            'anotherrelatedmodels/%s' % self.child.pk
        )

    def test_relate_get_reverse(self):
        response = self.client.get(
            '/anotherrelatedmodels/%s.json' % self.child.pk
        )
        self.assertIn('inverserelationships', response.data)
        self.assertEqual(len(response.data['inverserelationships']), 1)
        invrel = response.data['inverserelationships'][0]
        self.assertEqual(invrel['type_label'], 'Child Of')
        self.assertEqual(invrel['item_id'], self.parent.pk)
        self.assertEqual(invrel['item_label'], str(self.parent))
        self.assertEqual(invrel['item_page'], 'relatedmodel')
        self.assertEqual(
            invrel['item_url'],
            'relatedmodels/%s' % self.parent.pk
        )

    def test_relate_post_forward_classic(self):
        form = {
            'name': 'Parent2',
            'relationship-%s-item_id' % self.reltype.pk: self.child.pk,
        }
        self.validate_post_forward(form)

    def test_relate_post_forward_jsonform(self):
        form = {
            'name': 'Parent2',
            'relationships[0][type_id]': self.reltype.pk,
            'relationships[0][item_id]': self.child.pk,
        }
        self.validate_post_forward(form)

    def validate_post_forward(self, form):
        response = self.client.post('/relatedmodels.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data['name'], "Parent2")
        self.assertIn("relationships", response.data)
        self.assertEqual(len(response.data["relationships"]), 1)
        rel = response.data['relationships'][0]
        self.assertEqual(rel['item_label'], 'Child1')
        self.assertEqual(
            rel['item_url'],
            'anotherrelatedmodels/%s' % self.child.pk
        )
        self.assertEqual(self.child.inverserelationships.count(), 2)

    def test_relate_post_inverse_classic(self):
        form = {
            'name': 'Child2',
            'inverserelationship-%s-item_id' % self.reltype.pk: self.parent.pk
        }
        self.validate_post_inverse(form)

    def test_relate_post_inverse_jsonform(self):
        form = {
            'name': 'Child2',

            'inverserelationships[0][type_id]': self.reltype.pk,
            'inverserelationships[0][item_id]': self.parent.pk,
        }
        self.validate_post_inverse(form)

    def validate_post_inverse(self, form):
        response = self.client.post('/anotherrelatedmodels.json', form)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Child2")
        self.assertIn("inverserelationships", response.data)
        self.assertEqual(len(response.data["inverserelationships"]), 1)
        invrel = response.data['inverserelationships'][0]
        self.assertEqual(invrel['item_label'], 'Parent1')
        self.assertEqual(
            invrel['item_url'],
            'relatedmodels/%s' % self.parent.pk
        )
        self.assertEqual(self.parent.relationships.count(), 2)

    def test_relate_put_forward_classic(self):
        child2 = AnotherRelatedModel.objects.create(name="Child2")
        relid = self.parent.relationships.all()[0].pk
        form = {
            'name': 'Parent1 - Updated',
            'relationship-%s-item_id' % self.reltype.pk: child2.pk,
            'relationship-%s-id' % self.reltype.pk: relid
        }
        self.validate_put_forward(form)

    def test_relate_put_forward_jsonform(self):
        child2 = AnotherRelatedModel.objects.create(name="Child2")
        relid = self.parent.relationships.all()[0].pk
        form = {
            'name': 'Parent1 - Updated',
            'relationships[0][id]': relid,
            'relationships[0][type_id]': self.reltype.pk,
            'relationships[0][item_id]': child2.pk,
        }
        self.validate_put_forward(form)

    def validate_put_forward(self, form):
        child2 = AnotherRelatedModel.objects.get(name="Child2")
        response = self.client.put(
            '/relatedmodels/%s.json' % self.parent.pk,
            form
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.parent = RelatedModel.objects.get(pk=self.parent.pk)
        self.assertEqual(self.parent.name, "Parent1 - Updated")
        self.assertIn("relationships", response.data)
        self.assertEqual(len(response.data["relationships"]), 1)

        rel = self.parent.relationships.all()[0]
        self.assertEqual(rel.right, child2)

        rel = response.data["relationships"][0]
        self.assertEqual(rel['item_id'], child2.pk)

    def test_relate_put_inverse_classic(self):
        parent2 = RelatedModel.objects.create(name="Parent2")
        relid = self.child.inverserelationships.all()[0].pk
        form = {
            'name': 'Child1 - Updated',
            'inverserelationship-%s-item_id' % self.reltype.pk: parent2.pk,
            'inverserelationship-%s-id' % self.reltype.pk: relid,
        }
        self.validate_put_inverse(form)

    def test_relate_put_inverse_jsonform(self):
        parent2 = RelatedModel.objects.create(name="Parent2")
        relid = self.child.inverserelationships.all()[0].pk
        form = {
            'name': 'Child1 - Updated',

            'inverserelationships[0][id]': relid,
            'inverserelationships[0][type_id]': self.reltype.pk,
            'inverserelationships[0][item_id]': parent2.pk,
        }
        self.validate_put_inverse(form)

    def validate_put_inverse(self, form):
        parent2 = RelatedModel.objects.get(name="Parent2")
        response = self.client.put(
            '/anotherrelatedmodels/%s.json' % self.child.pk,
            form
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.child = AnotherRelatedModel.objects.get(pk=self.child.pk)
        self.assertEqual(self.child.name, "Child1 - Updated")
        self.assertIn("inverserelationships", response.data)
        self.assertEqual(len(response.data["inverserelationships"]), 1)

        invrel = self.child.inverserelationships.all()[0]
        self.assertEqual(invrel.right, parent2)

        invrel = response.data["inverserelationships"][0]
        self.assertEqual(invrel['item_id'], parent2.pk)
