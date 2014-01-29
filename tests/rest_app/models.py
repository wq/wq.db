from wq.db.patterns import models


class RootModel(models.IdentifiedModel):
    description = models.TextField()


class OneToOneModel(models.Model):
    root = models.OneToOneField(RootModel)
