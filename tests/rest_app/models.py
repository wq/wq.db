from wq.db.patterns import models


class RootModel(models.IdentifiedModel):
    description = models.TextField()


class OneToOneModel(models.Model):
    root = models.OneToOneField(RootModel)

    def __unicode__(self):
        return "onetoonemodel for %s" % self.root


class ForeignKeyModel(models.Model):
    root = models.ForeignKey(RootModel)

    def __unicode__(self):
        return "foreignkeymodel for %s" % self.root


class ExtraModel(models.Model):
    root = models.ForeignKey(RootModel, related_name="extramodels")

    def __unicode__(self):
        return "extramodel for %s" % self.root
