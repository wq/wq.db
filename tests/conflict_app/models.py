from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        """
        Return the string representation of this object.

        Args:
            self: (todo): write your description
        """
        return self.name


class TestModel(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        """
        Return the string representation of this object.

        Args:
            self: (todo): write your description
        """
        return self.name
