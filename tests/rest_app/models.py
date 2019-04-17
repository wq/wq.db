from django.db import models
from django.utils.translation import ugettext_lazy as _
from wq.db.patterns.models import LabelModel
import time


class RootModel(LabelModel):
    slug = models.SlugField()
    description = models.TextField()

    wq_label_template = "{{slug}}"


class OneToOneModel(LabelModel):
    root = models.OneToOneField(RootModel, models.CASCADE)

    wq_label_template = "onetoonemodel for {{root}}"


class ForeignKeyModel(LabelModel):
    root = models.ForeignKey(RootModel, models.CASCADE)

    wq_label_template = "foreignkeymodel for {{root}}"


class ExtraModel(LabelModel):
    root = models.ForeignKey(
        RootModel,
        models.CASCADE,
        related_name="extramodels",
    )
    alt_root = models.ForeignKey(
        RootModel,
        models.CASCADE,
        related_name="extramodel_set",
        null=True,
        blank=True,
    )

    wq_label_template = "extramodel for {{root}}"


class UserManagedModel(models.Model):
    user = models.ForeignKey("auth.User", models.CASCADE)


class Parent(LabelModel):
    name = models.CharField(max_length=10)


class Child(LabelModel):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(Parent, models.CASCADE, related_name="children")


class ItemType(LabelModel):
    name = models.CharField(max_length=10)
    active = models.NullBooleanField(default=True)


class Item(LabelModel):
    name = models.CharField(max_length=10)
    type = models.ForeignKey(ItemType, models.CASCADE)


class FileModel(LabelModel):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='files')


class ImageModel(LabelModel):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='files')


class SlugModel(LabelModel):
    code = models.SlugField()
    name = models.CharField(max_length=255)


class SlugRefParent(LabelModel):
    ref = models.ForeignKey(SlugModel, models.CASCADE)
    name = models.CharField(max_length=255)

    wq_label_template = "{{name}}{{#ref_id}} ({{ref}}){{/ref_id}}"


class SlugRefChild(models.Model):
    parent = models.ForeignKey(SlugRefParent, models.CASCADE)
    name = models.CharField(max_length=255)


class DateModel(models.Model):
    name = models.CharField(max_length=10)
    date = models.DateTimeField()
    empty_date = models.DateTimeField(null=True)

    def __str__(self):
        return "%s on %s" % (self.name, self.date.date())


class ChoiceModel(LabelModel):
    CHOICE_CHOICES = [
        ('one', 'Choice One'),
        ('two', 'Choice Two'),
        ('three', 'Choice Three'),
    ]
    name = models.CharField(
        max_length=10,
        help_text='Enter Name',
    )
    choice = models.CharField(
        max_length=10,
        help_text='Pick One',
        choices=CHOICE_CHOICES,
    )

    wq_label_template = "{{name}}: {{choice}}"


class TranslatedModel(models.Model):
    name = models.CharField(
        verbose_name=_('translated model name'),
        max_length=255,
    )


class CharFieldModel(models.Model):
    required_field = models.CharField(max_length=20)
    nullable_field = models.CharField(null=True, max_length=20)
    blankable_field = models.CharField(blank=True, max_length=20)
    nullableblankable_field = models.CharField(
        null=True, blank=True, max_length=20
    )


class ExpensiveField(models.CharField):
    def __init__(self, cost=None, **kwargs):
        self.cost = cost
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['cost'] = self.cost
        return name, path, args, kwargs

    def to_python(self, value):
        if value:
            time.sleep(self.cost)
        return super().to_python(value)


class ExpensiveModel(LabelModel):
    name = models.CharField(max_length=20)
    expensive = ExpensiveField(cost=2, max_length=255)
    more_expensive = ExpensiveField(
        cost=5,
        max_length=255,
        null=True,
        blank=True
    )
