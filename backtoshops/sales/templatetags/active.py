import re
from django import template
from django.core.urlresolvers import RegexURLResolver
from backend import urls

register = template.Library()

@register.simple_tag
def active(request, pattern=''):
    path = request.path[1:] # Strip the leading /

    if pattern == '':
        return ''

    if re.search(pattern, path):
        return 'on'
    else:
        return ''