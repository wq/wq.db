from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from wq.db.patterns.base.models import NaturalKeyModelManager, NaturalKeyModel
from django.template.defaultfilters import slugify
from django.conf import settings
INSTALLED = ('wq.db.patterns.identify' in settings.INSTALLED_APPS)


WQ_IDENTIFIER_ORDER = getattr(
    settings, "WQ_IDENTIFIER_ORDER",
    ["-is_primary", "authority", "name"]
)


class IdentifierManager(models.Manager):
    _cache = {}

    @classmethod
    def update_cache(cls, ident):
        key = '%s-%s' % (ident.content_type_id, ident.object_id)
        cls._cache[key] = ident

    def get_for_object(self, obj):
        ct = ContentType.objects.get_for_model(obj)
        key = '%s-%s' % (ct.pk, obj.pk)
        cache = type(self)._cache
        if key in cache:
            return cache[key]
        ids = self.filter(content_type=ct, object_id=obj.pk, is_primary=True)
        if ids.count() > 0:
            cache[key] = ids[0]
            return cache[key]
        return None

    def filter_by_identifier(self, identifier):
        return self.filter(
            models.Q(slug=identifier) | models.Q(name=identifier)
        ).order_by('-is_primary')

    def resolve(self, identifiers, exclude_apps=[]):
        resolved = None
        unresolved = None
        for identifier in identifiers:
            ids = self.filter_by_identifier(identifier)
            if exclude_apps:
                ids = ids.exclude(content_type__app_label__in=exclude_apps)
            items = ids.order_by(
                'content_type', 'object_id'
            ).distinct('content_type', 'object_id').count()
            if items == 1:
                if resolved is None:
                    resolved = {}
                resolved[identifier] = ids[0]
            else:
                if unresolved is None:
                    unresolved = {}
                unresolved[identifier] = ids
        return resolved, unresolved

    # Default implementation of get_or_create doesn't work well with generics
    def get_or_create(self, **kwargs):
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            return self.create(**kwargs), True

    def find_unique_slug(self, name, model):
        if len(name) > 45:
            name = name[:45]
        slug = slugify(name)
        exists = self.filter(
            content_type__model=model,
            slug=slug
        )
        num = ''
        while exists.count() > 0:
            slug = slugify('%s %s' % (name, num))
            exists = self.filter(
                content_type__model=model,
                slug=slug
            )
            if num == '':
                num = 1
            else:
                num += 1
        return slug


class Identifier(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(blank=True)
    authority = models.ForeignKey('Authority', blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    # Identifer can contain a pointer to any model
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    objects = IdentifierManager()

    @property
    def url(self):
        if (not self.authority or not self.authority.object_url):
            return None
        else:
            return self.authority.object_url % self.slug

    def save(self, *args, **kwargs):
        if self.slug is None or self.slug == '':
            model = self.content_type.name
            self.slug = type(self).objects.find_unique_slug(self.name, model)
        super(Identifier, self).save(*args, **kwargs)
        if self.is_primary:
            IdentifierManager.update_cache(self)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'wq_identifier'
        ordering = WQ_IDENTIFIER_ORDER
        abstract = not INSTALLED


class PrimaryIdentifierManager(IdentifierManager):
    use_for_related_fields = True

    def get_queryset(self):
        qs = super(PrimaryIdentifierManager, self).get_queryset()
        return qs.filter(is_primary=True)


class PrimaryIdentifier(Identifier):
    objects = PrimaryIdentifierManager()

    class Meta:
        proxy = INSTALLED


class IdentifiedModelManager(NaturalKeyModelManager):
    def get_by_identifier(self, identifier, auto_create=False):
        searches = [
            {'identifiers__slug': identifier, 'identifiers__is_primary': True},
            {'identifiers__name': identifier, 'identifiers__is_primary': True},
            {'identifiers__slug': identifier},
            {'identifiers__name': identifier},
            {'pk': identifier}
        ]

        object = None
        for search in searches:
            try:
                object = self.get(**search)
                break
            except (ValueError, self.model.DoesNotExist):
                if 'pk' not in search:
                    continue
                elif (not auto_create):
                    name = self.model._meta.object_name
                    raise self.model.DoesNotExist(
                        '%s "%s" does not exist' % (name, identifier)
                    )

        if object is None and auto_create:
            object = self.create_by_natural_key(identifier)

        return object

    def get_by_natural_key(self, identifier):
        return self.get_by_identifier(identifier)

    def create_by_natural_key(self, identifier):
        if ('name' in self.model._meta.get_all_field_names()):
            object = self.create(name=identifier)
        else:
            object = self.create()
        object.identifiers.create(name=identifier, is_primary=True)
        return object

    def get_queryset(self):
        qs = super(IdentifiedModelManager, self).get_queryset()
        meta = self.model._meta
        if meta.ordering:
            return qs
        ct = ContentType.objects.get_for_model(self.model)
        query = (
            """ SELECT name FROM wq_identifier
                WHERE content_type_id=%s AND object_id=%s.%s AND is_primary
                LIMIT 1 """
            % (ct.pk, meta.db_table, meta.pk.get_attname_column()[1]))
        qs = qs.extra(select={'wq_id_name': query})
        return qs.order_by('wq_id_name')


class IdentifiedModel(NaturalKeyModel):
    identifiers = GenericRelation(Identifier)
    primary_identifiers = GenericRelation(PrimaryIdentifier)
    objects = IdentifiedModelManager()

    @classmethod
    def get_natural_key_fields(cls):
        return ['primary_identifiers__slug']

    @property
    def primary_identifier(self):
        return Identifier.objects.get_for_object(self)

    def fallback_identifier(self):
        if hasattr(self, 'name'):
            return str(self.name)
        else:
            return ContentType.objects.get_for_model(self).name

    def __str__(self):
        if self.primary_identifier:
            return self.primary_identifier.name
        else:
            return self.fallback_identifier()

    def natural_key(self):
        if self.primary_identifier:
            return (self.primary_identifier.slug,)
        else:
            return (self.pk,)

    class Meta:
        abstract = True


class Authority(models.Model):
    name = models.CharField(max_length=255)
    homepage = models.URLField(null=True, blank=True)
    object_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'authorities'
        db_table = 'wq_identifiertype'
        abstract = not INSTALLED
