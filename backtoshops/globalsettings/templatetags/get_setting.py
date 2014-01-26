from django import template
from globalsettings import get_setting as _get

register = template.Library()

@register.simple_tag
def get_setting(key):
    return _get(key)

