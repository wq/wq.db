# Use Django's template loader with Pystache's renderer

from pystache.renderer import Renderer as PystacheRenderer
from django.template.loaders.filesystem import Loader as FileSystemLoader


class Renderer(PystacheRenderer):
    def get_template_source(self, name):
        template, origin = Loader().load_template(name)
        return template.source

    def _make_load_template(self):
        return self.get_template_source

    def _make_load_partial(self):
        def load_partial(name):
            return self.get_template_source('partials/' + name + '.html')
        return load_partial

renderer = Renderer()


class Template(object):
    def __init__(self, source):
        #save raw source for actual rendering by Pystache
        self.source = source

    def render(self, context):
        return renderer.render(self.source, *context)


class Loader(FileSystemLoader):
    def load_template(self, template_name, template_dirs=None):
        source, origin = self.load_template_source(
            template_name, template_dirs
        )
        template = Template(source)
        return template, origin
