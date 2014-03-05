from django import template
from common.utils import is_shop_manager as _is_shop_manager

register = template.Library()

@register.simple_tag
@register.filter
def is_shop_manager(pk):
    return _is_shop_manager(pk)
