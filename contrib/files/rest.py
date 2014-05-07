from wq.db.rest import app
from .serializers import FileSerializer
from .models import FileType
import swapper
File = swapper.load_model('files', 'File')

app.router.register_model(FileType)
app.router.register_model(File, serializer=FileSerializer)
