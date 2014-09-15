from django.contrib import admin
from django.contrib.contenttypes import generic

from .models import Markdown

try:
    from django_markdown.admin import MarkdownInlineAdmin as InlineAdmin
except ImportError:
    from django.contrib.admin import StackedInline as InlineAdmin


class MarkdownInline(generic.GenericTabularInline, InlineAdmin):
    model = Markdown
    extra = 0


class MarkedModelAdmin(admin.ModelAdmin):
    inlines = [
        MarkdownInline
    ]
