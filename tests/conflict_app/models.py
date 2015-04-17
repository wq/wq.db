from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name
