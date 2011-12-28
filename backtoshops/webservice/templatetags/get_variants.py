from django import template
from attributes.models import BrandAttribute

register = template.Library()

@register.filter
def get_variants(value, arg):
	return BrandAttribute.objects.filter(product__sale__mother_brand=value)\
								 .distinct()\
								 .filter(product__type=arg)\
								 .distinct()

