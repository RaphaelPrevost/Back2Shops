from django import template
from common.constants import TARGET_MARKET_TYPES

register = template.Library()

@register.simple_tag
@register.filter
def is_global_sale(sale):
    return sale.type_stock == TARGET_MARKET_TYPES.GLOBAL

