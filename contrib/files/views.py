from rest_framework.response import Response
from wq.db.rest.views import View
from wq.db.rest.renderers import binary_renderer
from .util import generate_image


class GenerateView(View):
    renderer_classes = [binary_renderer('image/jpeg')]

    def get(self, request, size, image):
        data = generate_image(image, size)
        return Response(data.read())
