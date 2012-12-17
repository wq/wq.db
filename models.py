from wq.db.annotate.models import *
from wq.db.identify.models import *
from wq.db.locate.models   import *
from wq.db.relate.models   import *
from wq.db.files.models    import *

class IdentifiedRelatedModelManager(IdentifiedModelManager, RelatedModelManager):
    pass

class IdentifiedRelatedModel(IdentifiedModel, RelatedModel):
    objects = IdentifiedRelatedModelManager()
    class Meta:
        abstract = True
