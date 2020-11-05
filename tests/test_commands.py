from .base import APITestCase
from django.core.management import call_command
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import json


class CommandTestCase(APITestCase):
    def check_config(self, text):
        """
        Check the text.

        Args:
            self: (todo): write your description
            text: (str): write your description
        """
        data = json.loads(text)
        self.assertIn('pages', data)
        page = list(data['pages'].values())[0]
        self.assertIn('url', page)

    def test_dump_config_json(self):
        """
        Dumps config toml.

        Args:
            self: (todo): write your description
        """
        f = StringIO()
        call_command('dump_config', stdout=f)
        self.check_config(f.getvalue())

    def test_dump_config_amd(self):
        """
        Dump the test config dump to the test config.

        Args:
            self: (todo): write your description
        """
        f = StringIO()
        call_command('dump_config', format='amd', stdout=f)
        text = f.getvalue().strip()
        self.assertTrue(
            text.startswith('define('), "Unexpected start: %s..." % text[:10]
        )
        self.assertTrue(
            text.endswith(');'), "Unexpected end: ...%s" % text[-10:]
        )
        text = text.replace('define(', '')
        text = text.replace(');', '')
        self.check_config(text)
