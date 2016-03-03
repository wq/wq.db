from rest_framework.test import APITestCase
from rest_framework import status
from tests.rest_app.models import (
    RootModel, OneToOneModel, ForeignKeyModel, ExtraModel, UserManagedModel,
    Parent, Child, ItemType, Item, SlugModel,
)
from django.contrib.auth.models import User


class TemplateTestCase(APITestCase):
    def setUp(self):
        instance = RootModel.objects.create(
            slug='instance',
            description="Test"
        )
        for cls in OneToOneModel, ForeignKeyModel, ExtraModel:
            cls.objects.create(
                root=instance,
            )
        user = User.objects.create(username="testuser", is_superuser=True)
        self.client.force_authenticate(user)
        UserManagedModel.objects.create(id=1, user=user)
        parent = Parent.objects.create(name="Test", pk=1)
        parent.children.create(name="Test 1")
        parent.children.create(name="Test 2")
        itype = ItemType.objects.create(name="Test", pk=1)
        itype.item_set.create(name="Test 1")
        itype.item_set.create(name="Test 2")
        SlugModel.objects.create(
            code="test",
            name="Test",
        )

    def check_html(self, url, expected_html):
        response = self.client.get(url)
        self.assertTrue(status.is_success(response.status_code), response.data)
        html = response.content.decode('utf-8')
        self.assertHTMLEqual(expected_html, html)

    # Test url="" use case
    def test_template_list_at_root(self):
        self.check_html("/", """
            <ul>
              <li><a href="/instance">instance</a></li>
            </ul>
        """)

    def test_template_detail_at_root(self):
        instance = RootModel.objects.get(slug='instance')
        self.check_html("/instance", """
            <h1>instance</h1>
            <p>Test</p>
            <h3>OneToOneModel</h3>
            <p>
              <a href="/onetoonemodels/{onetoone_pk}">
                onetoonemodel for instance
              </a>
            </p>
            <h3>ExtraModels</h3>
            <ul>
              <li>
                <a href="/extramodels/{extra_pk}">
                  extramodel for instance
                </a>
              </li>
            </ul>
            <p><a href="/instance/edit">Edit</a></p>
        """.format(
            onetoone_pk=instance.onetoonemodel.pk,
            extra_pk=instance.extramodels.all()[0].pk,
        ))

    def test_template_filter_by_parent(self):
        childs = Parent.objects.get(pk=1).children.order_by('pk')
        self.check_html('/parents/1/children', """
            <p>2 Records</p>
            <h3>Childs for <a href="/parents/1">Test</a></h3>
            <ul>
              <li><a href="/children/{c1_pk}">Test 1</a></li>
              <li><a href="/children/{c2_pk}">Test 2</a></li>
            </ul>
        """.format(
            c1_pk=childs[0].pk,
            c2_pk=childs[1].pk,
        ))

        items = ItemType.objects.get(pk=1).item_set.order_by('pk')
        self.check_html('/itemtypes/1/items', """
            <h3><a href="/itemtypes/1">Test</a> Items</h3>
            <ul>
              <li><a href="/items/{i1_pk}">Test 1</a></li>
              <li><a href="/items/{i2_pk}">Test 2</a></li>
            </ul>
        """.format(
            i1_pk=items[0].pk,
            i2_pk=items[1].pk,
        ))

    def test_template_detail_user_serializer(self):
        self.check_html('/usermanagedmodels/1', """
            <h1>Object #1</h1>
            <p>Created by testuser</p>
            <p></p>
        """)

    def test_template_custom_lookup(self):
        self.check_html('/slugmodels/test', "<h1>Test</h1>")

    def test_template_default_per_page(self):
        parent = Parent.objects.get(pk=1)
        parent.name = "Test 1"
        parent.save()
        for i in range(2, 101):
            Parent.objects.create(
                id=i,
                name="Test %s" % i,
            )

        html = """
            <p>100 Records</p>
            <div>
              <h3>Page 1 of 2</h3>
              <a href="http://testserver/parents/?page=2">Next 50</a>
            </div>
            <ul>
        """
        for i in range(1, 51):
            html += """
                <li><a href="/parents/{pk}">Test {pk}</a></li>
            """.format(pk=i)
        html += """
           </ul>
        """
        self.check_html("/parents/", html)

    def test_template_custom_per_page(self):
        for i in range(3, 102):
            child = Child.objects.create(
                name="Test %s" % i,
                parent_id=1,
            )

        self.check_html("/children/?page=2", """
           <p>101 Records</p>
           <div>
             <a href="http://testserver/children/">Prev 100</a>
             <h3>Page 2 of 2</h3>
           </div>
           <ul>
             <li><a href="/children/{pk}">Test 101</a></li>
           </ul>
        """.format(pk=child.pk))

    def test_template_limit(self):
        for i in range(3, 101):
            child = Child.objects.create(
                name="Test %s" % i,
                parent_id=1,
            )
        html = """
            <p>100 Records</p>
            <div>
              <h3>Page 1 of 10</h3>
              <a href="http://testserver/children/?limit=10&page=2">Next 10</a>
            </div>
            <ul>
        """
        for child in Child.objects.all()[:10]:
            html += """
                <li><a href="/children/{pk}">{label}</a></li>
            """.format(pk=child.pk, label=child.name)
        html += """
           </ul>
        """
        self.check_html("/children/?limit=10", html)

    def test_template_context_processors(self):
        resp = self.client.get('/rest_context')
        token = resp.cookies['csrftoken'].value
        self.check_html("/rest_context", """
            <p>/rest_context</p>
            <p>0.0.0</p>
            <p>
              <input name="csrfmiddlewaretoken" type="hidden" value="{csrf}">
            </p>
            <p>rest_context</p>
            <p>Can Edit Items</p>
        """.format(csrf=token))

    def test_template_page_config(self):
        item = Item.objects.get(name="Test 1")
        self.check_html('/items/%s' % item.pk, """
            <h3>Test 1</h3>
            <a href="/itemtypes/1">Test</a>
            <a href="/items/{pk}/edit">Edit</a>
        """.format(pk=item.pk))
