# Use Django's template loader with Pystache's renderer
# NOTE: Support for multiple template engines was introduced in Django 1.8.
# This code includes hacks to support both 1.7 and 1.8.  When 1.9 comes out and
# we drop support for 1.7, we should be able to clean this up a bit.
from pystache.renderer import Renderer as PystacheRenderer
from django.template.loaders.filesystem import Loader as FileSystemLoader
from django.template.base import Template as DjangoTemplate
from django.utils.encoding import force_text
from django.utils.version import get_version

from django.utils.functional import empty
from django.utils.six import PY3
DJANGO18 = get_version() >= "1.8"


class Renderer(PystacheRenderer):
    def __init__(self, template, *args, **kwargs):
        self.template = template
        return super(Renderer, self).__init__(*args, **kwargs)

    def get_template_source(self, name):
        kwargs = {}
        if self.template.engine:
            kwargs['engine'] = self.template.engine
        template, origin = Loader(**kwargs).load_template(name)
        return template.source

    def _make_load_template(self):
        return self.get_template_source

    def _make_load_partial(self):
        def load_partial(name):
            return self.get_template_source('partials/' + name + '.html')
        return load_partial

    def _make_resolve_context(self):
        resolve_context = super(Renderer, self)._make_resolve_context()
        if DJANGO18 and PY3:
            return resolve_context

        def resolve(context, name):
            value = resolve_context(context, name)
            # Unwrap Django SimpleLazyObject
            if hasattr(value, '_wrapped'):
                if value._wrapped is empty:
                    value._setup()
                return value._wrapped
            return value
        return resolve

    def str_coerce(self, val):
        if val is None:
            return ""
        return force_text(val)


class Template(DjangoTemplate):
    def __init__(self, source, engine):
        # save raw source for actual rendering by Pystache
        self.source = source
        self.engine = engine

    def _render(self, context):
        renderer = Renderer(template=self)
        return renderer.render(self.source, *context)


class Loader(FileSystemLoader):
    def load_template(self, template_name, template_dirs=None):
        source, origin = self.load_template_source(
            template_name, template_dirs
        )
        template = Template(source, engine=getattr(self, 'engine', None))
        return template, origin
