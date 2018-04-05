def is_authenticated(request):
    return {
        'is_authenticated': request.user.is_authenticated()
    }
