from django import template
from shops.models import Shop
from common.utils import get_currency as _get_currency

register = template.Library()

@register.assignment_tag
def get_currency(user, id_shop):
    shop = Shop.objects.filter(pk=id_shop)
    if not shop:
        return ""
    else:
        shop = shop[0]
    return _get_currency(user, shop)
