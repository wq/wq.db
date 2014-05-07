from wq.db.rest import app
from .views import FileViewSet

import swapper
File = swapper.load_model('files', 'File')

app.router.register_model(File, viewset=FileViewSet)
