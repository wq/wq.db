from django.contrib.contenttypes.models import (
    ContentType as DjangoContentType,
    ContentTypeManager as DjangoContentTypeManager
)
from django.utils.encoding import force_text
from .model_tools import get_ct, get_object_id, get_by_identifier


__all__ = (
    'ContentType',
    'get_ct',
    'get_object_id',
    'get_by_identifier',
)


class ContentTypeManager(DjangoContentTypeManager):
    def get_by_identifier(self, identifier):
        return self.get(model=identifier)


class ContentType(DjangoContentType):
    objects = ContentTypeManager()

    @property
    def identifier(self):
        return self.model

    @property
    def urlbase(self):
        cls = self.model_class()
        if cls is None:
            return None
        config = self.get_config()
        if config:
            return config['url']
        urlbase = force_text(cls._meta.verbose_name_plural)
        return urlbase.replace(' ', '')

    # Get foreign keys for this content type
    def get_foreign_keys(self):
        cls = self.model_class()
        if cls is None:
            return []
        parents = {}
        for f in cls._meta.fields:
            if f.rel is not None and type(f.rel).__name__ == 'ManyToOneRel':
                parent = get_ct(f.rel.to)
                parents.setdefault(parent, [])
                parents[parent].append(f.name)
        return parents

    def get_parents(self):
        return set(self.get_foreign_keys().keys())

    def get_children(self, include_rels=False):
        cls = self.model_class()
        if cls is None:
            return []
        # get_all_related_objects() removed in Django 1.10
        rels = [
            field for field in cls._meta.get_fields()
            if (field.one_to_many or field.one_to_one)
            and field.auto_created and not field.concrete
        ]

        # get_all_related_objects() structure changed in Django 1.8
        def get_model(rel):
            return getattr(rel, 'related_model', rel.model)

        children = [(get_ct(get_model(rel)), rel) for rel in rels]
        if include_rels:
            return set(children)
        else:
            return set(child[0] for child in children)

    def get_config(self, user=None):
        from . import router  # avoid circular import
        cls = self.model_class()
        return router.get_model_config(cls, user)

    def is_registered(self):
        from . import router  # avoid circular import
        cls = self.model_class()
        return router.model_is_registered(cls)

    class Meta:
        proxy = True
