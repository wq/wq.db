from django.db import models
import pystache


class LabelModel(models.Model):
    wq_label_template = "{{name}}"

    def __str__(self):
        return pystache.render(self.wq_label_template, self)

    class Meta:
        abstract = True
