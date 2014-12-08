from django import template
from accounts.models import Brand
from common.assets_utils import get_full_url

register = template.Library()

@register.simple_tag
@register.filter
def brand_ico(user):
    brand_id = user.get_profile().work_for.id
    br = Brand.objects.get(pk=brand_id)
    if not br.logo:
        return ""
    logo = get_full_url(str(br.logo))
    return logo
