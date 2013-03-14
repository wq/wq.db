from pystache.renderers import Renderer

from django.template import load_template
from django.template.loaders.filesystem import Loader

# Use Django's template loader but Pystache's renderer

class Renderer(Renderer):
    def get_template_source(self, name):
        return load_template(name).source
        
    def _make_load_template(self): 
        return self.get_template_source

class Template(object):
    def __init__(self, source):
        self.source = source
    def render(self, context):
        return renderer.render(self.source, *context)

class Loader(Loader):
    def load_template(self, template_name, template_dirs=None):
        source, origin = self.load_template_source(template_name, template_dirs)
        template = Template(source)
        return template, origin
