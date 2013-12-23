from wq.db.patterns import models


class RootModel(models.IdentifiedModel):
    description = models.TextField()


class AnnotatedModel(models.AnnotatedModel):
    name = models.CharField(max_length=255)
