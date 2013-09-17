from django.forms import ModelForm, Select
from itertools import chain

# Until https://code.djangoproject.com/ticket/15602 is fixed, we need a way
# to make the 'type' field readonly for existing annotations in an
# AnnotationInline. This is done here by extending the Select widget.


class SelectOnce(Select):
    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            return super(SelectOnce, self).render(name, value, attrs, choices)
        else:
            for option_value, option_label in chain(self.choices, choices):
                if str(option_value) == str(value):
                    return (
                        "<p>%s</p><input type='hidden' name='%s' value='%s'>"
                        % (option_label, name, value)
                    )
        return "<p>Not Found</p>"


class AnnotationForm(ModelForm):
    class Meta:
        widgets = {
            'type': SelectOnce
        }
