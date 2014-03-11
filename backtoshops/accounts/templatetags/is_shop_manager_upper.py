from django import template
from common.utils import is_shop_manager_upper as _is_shop_manager_upper

register = template.Library()

@register.simple_tag
@register.filter
def is_shop_manager_upper(user):
    if user.is_superuser:
        return True
    return _is_shop_manager_upper(user.get_profile().pk)
