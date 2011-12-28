from django import template

register = template.Library()

@register.filter
def getform(value, arg):
    return value[arg-1]