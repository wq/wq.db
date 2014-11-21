from .app import router


def version(request):
    return {'version': router.version}


def pages_info(request):
    info = {
        'base_url': "",
        'full_path': request.path,
        'path': request.path[1:],
        'prev_path': '',  # Referer?
        'params': request.GET,
    }

    return {
        'pages_info': info
    }
