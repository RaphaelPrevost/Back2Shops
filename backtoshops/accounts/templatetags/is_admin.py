from django import template
from common.constants import USERS_ROLE

register = template.Library()

@register.simple_tag
@register.filter
def is_admin(user):
    return (not user.is_superuser and
            user.get_profile().role == USERS_ROLE.ADMIN)

