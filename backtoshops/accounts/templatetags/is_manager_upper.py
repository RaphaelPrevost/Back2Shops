from django import template
from common.constants import USERS_ROLE

register = template.Library()

@register.simple_tag
@register.filter
def is_manager_upper(user):
    if user.is_superuser:
        return True
    return user.get_profile().role <= USERS_ROLE.MANAGER
