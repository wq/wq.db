from wq.db.patterns import models


class AnnotatedModel(models.AnnotatedModel):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name
