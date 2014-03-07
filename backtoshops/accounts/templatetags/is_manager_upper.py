from django import template
from common.constants import USERS_ROLE

register = template.Library()

@register.simple_tag
@register.filter
def is_manager_upper(role):
    return int(role) <= USERS_ROLE.MANAGER
