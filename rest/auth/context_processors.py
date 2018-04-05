def is_authenticated(request):
    return {
        'is_authenticated': bool(request.user.is_authenticated)
    }
