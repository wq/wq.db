from .base import APITestCase
from rest_framework import status
from tests.rest_app.models import (
    RootModel, OneToOneModel, ForeignKeyModel, ExtraModel, UserManagedModel,
    Parent, Child, ItemType, Item, SlugModel, SlugRefParent, ChoiceModel,
)
from django.contrib.auth.models import User
from django.conf import settings


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
        slugref = SlugModel.objects.create(
            code="test",
            name="Test",
        )
        SlugRefParent.objects.create(
            ref=slugref,
            pk=1,
            name="Test Slug Ref"
        )
        SlugRefParent.objects.create(
            ref=SlugModel.objects.create(
                code="other",
                name="Other",
            ),
            pk=2,
            name="Test Another Ref",
        )
        ItemType.objects.create(
            name="Inactive",
            pk=2,
            active=False
        )
        ChoiceModel.objects.create(
            name="Test",
            pk=1,
            choice="two"
        )

    def assertHTMLEqual(self, expected_html, html, auto_replace=True):
        if settings.WITH_NONROOT and auto_replace:
            html = html.replace('/wqsite/', '/')
        super().assertHTMLEqual(expected_html, html)

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
        response = self.client.get('/rest_context')
        html = response.content.decode('utf-8')
        token = html.split('value="')[1].split('"')[0]
        self.assertTrue(len(token) >= 32)
        if settings.WITH_NONROOT:
            base_url = '/wqsite'
        else:
            base_url = ''
        self.assertHTMLEqual("""
            <p>{base_url}/rest_context</p>
            <p>rest_context</p>
            <p>{base_url}/</p>
            <p>{base_url}/</p>
            <p>0.0.0</p>
            <p>
              <input name="csrfmiddlewaretoken" type="hidden" value="{csrf}">
            </p>
            <p>rest_context</p>
            <p>Can Edit Items</p>
        """.format(csrf=token, base_url=base_url), html, auto_replace=False)

    def test_template_page_config(self):
        item = Item.objects.get(name="Test 1")
        self.check_html('/items/%s' % item.pk, """
            <h3>Test 1</h3>
            <a href="/itemtypes/1">Test</a>
            <a href="/items/{pk}/edit">Edit</a>
        """.format(pk=item.pk))

    def test_template_edit_fk(self):
        item = Item.objects.get(name="Test 1")
        self.check_html('/items/%s/edit' % item.pk, """
            <form>
              <input name="name" required value="Test 1">
              <select name="type_id" required>
                <option value="">Select one...</option>
                <option value="1" selected>Test</option>
                <option value="2">Inactive</option>
              </select>
              <button>Submit</button>
            </form>
        """)

    def test_template_edit_choice(self):
        self.check_html('/choicemodels/1/edit', """
            <form>
              <input name="name" required value="Test">
              <fieldset>
                <legend>Choice</legend>
                <input type="radio" id="choicemodel-choice-one"
                       name="choice" value="one">
                <label for="choicemodel-choice-one">Choice One</label>
                <input type="radio" id="choicemodel-choice-two"
                       name="choice" value="two" checked>
                <label for="choicemodel-choice-two">Choice Two</label>
                <input type="radio" id="choicemodel-choice-three"
                       name="choice" value="three">
                <label for="choicemodel-choice-three">Choice Three</label>
              </fieldset>
              <button>Submit</button>
            </form>
        """)

    def test_template_new_fk(self):
        self.check_html('/children/new', """
            <form>
              <input name="name" required value="">
              <select name="parent_id" required>
                <option value="">Select one...</option>
                <option value="1">Test</option>
              </select>
              <button>Submit</button>
            </form>
        """)

    def test_template_new_fk_filtered(self):
        self.check_html('/items/new', """
            <form>
              <input name="name" required value="">
              <select name="type_id" required>
                <option value="">Select one...</option>
                <option value="1">Test</option>
              </select>
              <button>Submit</button>
            </form>
        """)

    def test_template_new_fk_defaults(self):
        self.check_html('/items/new?type_id=1', """
            <form>
              <input name="name" required value="">
              <select name="type_id" required>
                <option value="">Select one...</option>
                <option value="1" selected>Test</option>
              </select>
              <button>Submit</button>
            </form>
        """)

    def test_template_new_fk_slug(self):
        self.check_html('/slugrefparents/new?ref_id=test', """
            <form>
              <input name="name" required value="">
              <select name="ref_id" required>
                <option value="">Select one...</option>
                <option value="test" selected>Test</option>
                <option value="other">Other</option>
              </select>
              <button>Submit</button>
            </form>
        """)

    def test_template_new_fk_slug_filtered(self):
        self.check_html('/slugrefchildren/new', """
            <form>
              <input name="name" required value="">
              <select name="parent_id" required>
                <option value="">Select one...</option>
                <option value="1">Test Slug Ref (Test)</option>
              </select>
              <button>Submit</button>
            </form>
        """)

    def test_template_new_choice(self):
        self.check_html('/choicemodels/new', """
            <form>
              <input name="name" required value="">
              <fieldset>
                <legend>Choice</legend>
                <input type="radio" id="choicemodel-choice-one"
                       name="choice" value="one">
                <label for="choicemodel-choice-one">Choice One</label>
                <input type="radio" id="choicemodel-choice-two"
                       name="choice" value="two">
                <label for="choicemodel-choice-two">Choice Two</label>
                <input type="radio" id="choicemodel-choice-three"
                       name="choice" value="three">
                <label for="choicemodel-choice-three">Choice Three</label>
              </fieldset>
              <button>Submit</button>
            </form>
        """)

    def test_template_new_choice_defaults(self):
        self.check_html('/choicemodels/new?choice=three', """
            <form>
              <input name="name" required value="">
              <fieldset>
                <legend>Choice</legend>
                <input type="radio" id="choicemodel-choice-one"
                       name="choice" value="one">
                <label for="choicemodel-choice-one">Choice One</label>
                <input type="radio" id="choicemodel-choice-two"
                       name="choice" value="two">
                <label for="choicemodel-choice-two">Choice Two</label>
                <input type="radio" id="choicemodel-choice-three"
                       name="choice" value="three" checked>
                <label for="choicemodel-choice-three">Choice Three</label>
              </fieldset>
              <button>Submit</button>
            </form>
        """)

    def test_script_tags(self):
        self.check_html('/script_context', """
            <html>
              <head>
                <script async>TEST</script>
                <script async src="chunk1.js"></script>
                <script async src="chunk2.js"></script>
              </head>
              <body>
              </body>
            </html>
        """)
