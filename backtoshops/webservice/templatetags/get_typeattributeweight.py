from django import template
from sales.models import TypeAttributeWeight

register = template.Library()

@register.filter
def get_typeattributeweight(value, arg):
    try:
        return TypeAttributeWeight.objects.get(sale=value,
                                               type_attribute=arg)
    except TypeAttributeWeight.DoesNotExist:
        return None
