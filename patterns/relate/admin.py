from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django import forms

from .models import (
    Relationship, InverseRelationship, RelatedModel,
    RelationshipType, InverseRelationshipType,
    INSTALLED,
)


class RelationshipForm(forms.ModelForm):
    if INSTALLED:
        type = forms.models.ModelChoiceField(
            queryset=RelationshipType.objects.filter(computed=False)
        )


class InverseRelationshipForm(forms.ModelForm):
    if INSTALLED:
        type = forms.models.ModelChoiceField(
            queryset=InverseRelationshipType.objects.filter(computed=False)
        )


class RelationshipInline(GenericTabularInline):
    model = Relationship
    ct_field = "from_content_type"
    ct_fk_field = "from_object_id"
    form = RelationshipForm
    extra = 0
    readonly_fields = ('to_content_object',)

    def get_queryset(self, request):
        return Relationship.objects.filter(computed=False)


class InverseRelationshipInline(GenericTabularInline):
    model = InverseRelationship
    ct_field = "to_content_type"
    ct_fk_field = "to_object_id"
    form = InverseRelationshipForm
    extra = 0
    readonly_fields = ('from_content_object',)

    def get_queryset(self, request):
        return InverseRelationship.objects.filter(computed=False)


class RelatedModelAdmin(admin.ModelAdmin):
    model = RelatedModel
    inlines = [
        RelationshipInline,
        InverseRelationshipInline
    ]
