from django import template
from common.utils import get_brand_currency as _get_brand_currency

register = template.Library()

@register.simple_tag
@register.filter
def get_brand_currency(user):
    return _get_brand_currency(user)
