from django import template
from common.constants import USERS_ROLE
from shops.models import Shop

register = template.Library()

@register.simple_tag
@register.filter
def show_step_shop(sale, user):
    if sale.shops.all():
        return True

    if Shop.objects.filter(mother_brand=sale.mother_brand):
        return True

    if (not user.is_superuser and
            user.get_profile().role in (USERS_ROLE.ADMIN, USERS_ROLE.MANAGER) and
            user.get_profile().allow_internet_operate and
            user.get_profile().shops.all()):
        return True

    return False

