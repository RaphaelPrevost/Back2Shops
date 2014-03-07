from django import template
from common.utils import is_shop_manager_upper as _is_shop_manager_upper

register = template.Library()

@register.simple_tag
@register.filter
def is_shop_manager_upper(pk):
    return _is_shop_manager_upper(pk)
