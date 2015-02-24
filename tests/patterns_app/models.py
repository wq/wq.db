from wq.db.patterns import models


class AnnotatedModel(models.AnnotatedModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class IdentifiedModel(models.IdentifiedModel):
    name = models.CharField(max_length=255)


class IdentifiedAnnotatedModel(models.IdentifiedModel, models.AnnotatedModel):
    name = models.CharField(max_length=255)


class MarkedModel(models.MarkedModel):
    name = models.CharField(max_length=255)


class LocatedModel(models.LocatedModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class RelatedModel(models.RelatedModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class AnotherRelatedModel(models.RelatedModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
