from django import template
from common.assets_utils import get_full_url

register = template.Library()

@register.filter
def no_thumbnail(value):
    return get_full_url("img/product_pictures/default_img.png")
