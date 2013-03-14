from rest_framework.renderers import JSONPRenderer

class AMDRenderer(JSONPRenderer):
    media_type = 'application/javascript'
    format = 'js'
    callback_parameter = 'define'
