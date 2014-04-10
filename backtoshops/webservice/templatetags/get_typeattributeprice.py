from django import template
from sales.models import TypeAttributePrice

register = template.Library()

@register.filter
def get_typeattributeprice(value, arg):
    try:
        return TypeAttributePrice.objects.get(sale=value,
                                              type_attribute=arg)
    except TypeAttributePrice.DoesNotExist:
        return None
