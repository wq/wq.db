from rest_framework.response import Response
from wq.db.rest.views import SimpleView
from wq.db.rest.renderers import binary_renderer
from wq.db.rest import app
from wq.db.patterns.base import swapper
from .serializers import FileSerializer
from .util import generate_image

File = swapper.load_model('files', 'File')


class GenerateView(SimpleView):
    renderer_classes = [binary_renderer('image/jpeg')]

    def get(self, request, size, image):
        data = generate_image(image, size)
        return Response(data.read())

app.router.register_model(File, serializer=FileSerializer)
