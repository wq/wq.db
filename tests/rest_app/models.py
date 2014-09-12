from wq.db.patterns import models


class RootModel(models.IdentifiedModel):
    description = models.TextField()


class OneToOneModel(models.Model):
    root = models.OneToOneField(RootModel)

    def __str__(self):
        return "onetoonemodel for %s" % self.root


class ForeignKeyModel(models.Model):
    root = models.ForeignKey(RootModel)

    def __str__(self):
        return "foreignkeymodel for %s" % self.root


class ExtraModel(models.Model):
    root = models.ForeignKey(RootModel, related_name="extramodels")

    def __str__(self):
        return "extramodel for %s" % self.root
