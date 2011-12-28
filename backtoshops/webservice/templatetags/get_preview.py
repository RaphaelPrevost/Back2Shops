from django import template
from attributes.models import BrandAttributePreview

register = template.Library()

@register.filter
def get_preview(value, arg):
	toret = BrandAttributePreview.objects.get(brand_attribute=value, product=arg)
	return toret
