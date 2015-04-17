from wq.db import rest
from .serializers import FileSerializer
from .models import FileType
import swapper
File = swapper.load_model('files', 'File')

rest.router.register_model(FileType)
rest.router.register_model(File, serializer=FileSerializer)
