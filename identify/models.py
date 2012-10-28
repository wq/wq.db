from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.template.defaultfilters import slugify

class IdentifierManager(models.Manager):
    def filter_by_identifier(self, identifier):
        searches = [
            {'slug': identifier, 'is_primary': True},
            {'name': identifier, 'is_primary': True},
            {'slug': identifier},
            {'name': identifier}
        ]
        for search in searches:
            ids = self.filter(**search)
            if len(ids) == 0:
                continue
            return ids
        return ids

    def resolve(self, *args):
        resolved   = None
        unresolved = None
        for identifier in args:
            ids = self.filter_by_identifier(identifier)
            if len(ids) == 1:
                if not resolved: resolved = {}
                resolved[identifier] = ids[0]
            else:
                if not unresolved: unresolved = {}
                unresolved[identifier] = ids
        return resolved, unresolved

    # Default implementation of get_or_create doesn't work well with generics
    def get_or_create(self, **kwargs):
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            return self.create(**kwargs), True

    def find_unique_slug(self, name, model):
        slug = slugify(name)
        exists = self.filter(
             content_type__name = model,
             slug               = slug
        )
        num = ''
        while exists.count() > 0:
            slug = slugify('%s %s' % (name, num))
            exists = self.filter(
                 content_type__name = model,
                 slug               = slug
            )
            if num == '':
                num = 1
            else:
                num += 1
        return slug


class Identifier(models.Model):
    name       = models.CharField(max_length=255, db_index=True)
    slug       = models.SlugField()
    authority  = models.ForeignKey('Authority', blank=True, null=True)
    is_primary = models.BooleanField()
    valid_from = models.DateField(blank=True, null=True)
    valid_to   = models.DateField(blank=True, null=True)

    # Identifer can contain a pointer to any model
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    objects = IdentifierManager()

    @property
    def url(self):
        if (self.authority is None or self.authority.object_url is None):
            return self.slug
	else:
            return self.authority.object_url % self.slug

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'wq_identifier'

class PrimaryIdentifierManager(IdentifierManager):
    use_for_related_fields = True

    def get_query_set(self):
        qs = super(PrimaryIdentifierManager, self).get_query_set()
        return qs.filter(is_primary=True)

class PrimaryIdentifier(Identifier):
    objects = PrimaryIdentifierManager()
    class Meta:
        proxy = True

class IdentifiedModelManager(models.Manager):
    def get_by_identifier(self, identifier, auto_create=False):
        searches = [
            {'identifiers__slug': identifier, 'identifiers__is_primary': True},
            {'identifiers__name': identifier, 'identifiers__is_primary': True},
            {'identifiers__slug': identifier},
            {'identifiers__name': identifier},
            {'pk':                identifier}
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
                    raise self.model.DoesNotExist

        if object is None and auto_create:
            if ('name' in self.model._meta.get_all_field_names()):
                object = self.create(name = identifier)
            else:
                object = self.create()
            object.identifiers.create(name = identifier, is_primary=True)

        return object

    def get_query_set(self):
        qs = super(IdentifiedModelManager, self).get_query_set()
        ct = ContentType.objects.get_for_model(self.model)
        meta = self.model._meta
        qs = qs.extra(select={'wq_id_name': """
               SELECT name FROM wq_identifier
               WHERE content_type_id=%s AND object_id=%s.%s AND is_primary
               LIMIT 1""" % (ct.pk, meta.db_table, meta.pk.get_attname_column()[1])})
        return qs.order_by('wq_id_name')

class IdentifiedModel(models.Model):
    identifiers = generic.GenericRelation(Identifier)
    primary_identifiers = generic.GenericRelation(PrimaryIdentifier, related_name='%(app_label)s_%(class)s_primary')
    objects     = IdentifiedModelManager()

    @property
    def primary_identifier(self):
        if self.primary_identifiers.count() > 0:
            return self.primary_identifiers.all()[0]
        return None

    def fallback_identifier(self):
        if hasattr(self, 'name'):
            return unicode(self.name)
        else:
            return ContentType.objects.get_for_model(self).name

    def __unicode__(self):
        if self.primary_identifier:
            return unicode(self.primary_identifier)
        else:
            return self.fallback_identifier()

    class Meta:
        abstract = True

class Authority(models.Model):
    name       = models.CharField(max_length=255)
    homepage   = models.URLField(null=True,blank=True)
    object_url = models.URLField(null=True,blank=True)

    class Meta:
        verbose_name_plural = 'authorities'
        db_table = 'wq_identifiertype'

    def __unicode__(self):
        return self.name
