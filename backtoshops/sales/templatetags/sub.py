from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    try:
        return value - arg
    except TypeError:
        return 'N/A'
