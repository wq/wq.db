from . import router
from django.utils.http import urlquote


def version(request):
    return {'version': router.version}


def router_info(request):
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
        'router_info': info,
        'pages_info': info,
    }


def pages_info(request):
    return router_info(request)


def wq_config(request):
    # FIXME: support non-root base_url
    parts = request.path.split('/')
    user = request.user if request.user.is_authenticated() else None
    wq_conf = router.get_config(user=user)
    page_conf = None
    root_conf = None

    for name, conf in wq_conf['pages'].items():
        if parts[1] == conf['url']:
            page_conf = conf
        elif conf['url'] == "":
            root_conf = conf

    if not page_conf and root_conf and len(parts) == 2:
        page_conf = root_conf

    return {
        'wq_config': wq_conf,
        'page_config': page_conf,
    }
