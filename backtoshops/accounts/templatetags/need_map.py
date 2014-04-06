from django import template

from common.constants import USERS_ROLE
from shops.models import Shop

register = template.Library()

@register.simple_tag
@register.filter
def need_map(user):
    if user.is_superuser:
        return False

    u_profile = user.get_profile()
    if u_profile.role == USERS_ROLE.ADMIN:
        shops = Shop.objects.filter(mother_brand=u_profile.work_for)
        return len(shops) > 1
    elif u_profile.role == USERS_ROLE.MANAGER:
        return len(u_profile.shops.all()) > 1
    return False
