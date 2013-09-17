from .app import router


def version(request):
    return {'version': router.version}
