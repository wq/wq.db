from .app import router
from django.utils.http import urlquote


def version(request):
    return {'version': router.version}


def pages_info(request):
    # FIXME: support non-root base_url
    base_url = ""
    path = request.path[1:]
    if request.GET:
        path += "?" + request.GET.urlencode()
    full_path = base_url + "/" + path

    info = {
        'base_url': base_url,
        'path': path,
        'path_enc': urlquote(path),
        'params': request.GET,
        'full_path': full_path,
        'full_path_enc': urlquote(full_path),
        'prev_path': '',  # Referer?
    }

    return {
        'pages_info': info
    }
