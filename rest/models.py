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
        """
        Get a model by its identifier.

        Args:
            self: (todo): write your description
            identifier: (str): write your description
        """
        # TODO: What if model is configured with a different name?
        return self.get(model=identifier)


class ContentType(DjangoContentType):
    objects = ContentTypeManager()

    @property
    def identifier(self):
        """
        Return the identifier of the model.

        Args:
            self: (todo): write your description
        """
        from . import router
        conf = router._config.get(self.model_class(), {})
        return conf.get('name', self.model)

    @property
    def urlbase(self):
        """
        Return base url.

        Args:
            self: (todo): write your description
        """
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
        """
        Returns a list of foreign keys

        Args:
            self: (todo): write your description
        """
        cls = self.model_class()
        if cls is None:
            return []
        parents = {}
        for f in cls._meta.fields:
            rel = f.remote_field
            if rel is not None and type(rel).__name__ == 'ManyToOneRel':
                parent = get_ct(rel.model)
                parents.setdefault(parent, [])
                parents[parent].append(f.name)
        return parents

    def get_parents(self):
        """
        Returns the set of this model.

        Args:
            self: (todo): write your description
        """
        return set(self.get_foreign_keys().keys())

    def get_children(self, include_rels=False):
        """
        Return a list of all relationships

        Args:
            self: (todo): write your description
            include_rels: (bool): write your description
        """
        cls = self.model_class()
        if cls is None:
            return []

        rels = [
            field for field in cls._meta.get_fields()
            if (field.one_to_many or field.one_to_one)
            and field.auto_created and not field.concrete
        ]

        children = [(get_ct(rel.related_model), rel) for rel in rels]
        if include_rels:
            return set(children)
        else:
            return set(child[0] for child in children)

    def get_config(self, user=None):
        """
        Get config : class : router : userconfig : : parameterconfigconfig object

        Args:
            self: (todo): write your description
            user: (todo): write your description
        """
        from . import router  # avoid circular import
        cls = self.model_class()
        return router.get_model_config(cls, user)

    def is_registered(self):
        """
        Return class of the model class.

        Args:
            self: (todo): write your description
        """
        from . import router  # avoid circular import
        cls = self.model_class()
        return router.model_is_registered(cls)

    class Meta:
        proxy = True
