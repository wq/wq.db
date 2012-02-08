from django.contrib.contenttypes import generic
from django.contrib import admin

from wq.identify.models import Identifier, IdentifiedModel, Authority

class IdentifierInline(generic.GenericTabularInline):
    model = Identifier
    prepopulated_fields = {"slug": ("name",)}
    extra = 0

class IdentifiedModelAdmin(admin.ModelAdmin):
    model = IdentifiedModel
    inlines = [
        IdentifierInline
    ]

class AuthorityIdentifierInline(admin.TabularInline):
    model = Identifier
    extra = 0

class AuthorityAdmin(admin.ModelAdmin):
    model = Authority
    inlines = [
        AuthorityIdentifierInline
    ]
