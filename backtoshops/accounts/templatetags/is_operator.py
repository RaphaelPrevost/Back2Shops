from django import template
from common.constants import USERS_ROLE

register = template.Library()

@register.simple_tag
@register.filter
def is_operate(user):
    return (not user.is_superuser and
            user.get_profile().role == USERS_ROLE.OPERATOR)

