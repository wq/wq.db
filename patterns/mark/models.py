from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from ..base.models import LabelModel
from django.utils.translation import get_language_from_request
from django.conf import settings

import swapper
swapper.set_app_prefix('mark', 'WQ')

INSTALLED = ('wq.db.patterns.mark' in settings.INSTALLED_APPS)


class BaseMarkdownType(LabelModel):
    name = models.CharField(max_length=100)

    @classmethod
    def get_current(cls, request=None):
        if request:
            try:
                kwargs = cls.get_current_filter(request)
                return cls.objects.get(**kwargs)
            except cls.DoesNotExist:
                pass
        return cls.get_default()

    @classmethod
    def get_current_filter(cls, request):
        raise NotImplementedError()

    @classmethod
    def get_default(cls):
        markdowns = cls.objects.all()
        if len(markdowns) > 0:
            return markdowns[0]

    class Meta:
        abstract = True
        ordering = ['pk']


class MarkdownType(BaseMarkdownType):
    @classmethod
    def get_current_filter(cls, request):
        lang = get_language_from_request(request)
        return {'name': lang}

    class Meta:
        swappable = swapper.swappable_setting('mark', 'MarkdownType')
        db_table = "wq_markdowntype"
        abstract = not INSTALLED


class Markdown(models.Model):
    type = models.ForeignKey(swapper.get_model_name('mark', 'MarkdownType'))
    summary = models.CharField(max_length=255, null=True, blank=True)
    markdown = models.TextField(null=True, blank=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        return self.summary or ''

    @property
    def html(self):
        from markdown import markdown
        extensions = getattr(settings, 'MARKDOWN_EXTENSIONS', [])
        return markdown(self.markdown, extensions)

    class Meta:
        db_table = "wq_markdown"
        abstract = not INSTALLED


class MarkedModel(models.Model):
    markdown = GenericRelation(Markdown)

    def get_markdown(self, type):
        markdowns = self.markdown.filter(type=type)
        if len(markdowns) == 0:
            markdowns = self.markdown.order_by("type")
        if len(markdowns) > 0:
            return markdowns[0]
        return None

    def get_html(self, type):
        markdown = self.get_markdown(type)
        if markdown:
            return markdown.html
        return None

    class Meta:
        abstract = True
