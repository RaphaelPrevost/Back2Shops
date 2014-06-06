from django import template

register = template.Library()

@register.simple_tag
@register.filter
def multiply(value, arg):
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0
