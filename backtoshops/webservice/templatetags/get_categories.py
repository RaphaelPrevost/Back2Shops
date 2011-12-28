from django import template
from sales.models import ProductCategory

register = template.Library()

@register.filter
def get_categories(value):
	return ProductCategory.objects.filter(products__sale__mother_brand=value).distinct()
