from django import template
from common.constants import USERS_ROLE

register = template.Library()

@register.simple_tag
@register.filter
def is_admin_upper(user):
    return (user.is_superuser or
            user.get_profile().role == USERS_ROLE.ADMIN)

