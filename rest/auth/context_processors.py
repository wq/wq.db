def is_authenticated(request):
    """
    Returns whether the request is authenticated.

    Args:
        request: (todo): write your description
    """
    return {
        'is_authenticated': bool(request.user.is_authenticated)
    }
