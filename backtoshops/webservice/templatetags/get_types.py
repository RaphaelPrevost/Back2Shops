from django import template
from sales.models import ProductType

register = template.Library()

@register.filter
def get_types(value):
    return ProductType.objects.filter(products__sale__mother_brand=value).distinct()
