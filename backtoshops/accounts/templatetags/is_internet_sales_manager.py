from django import template

register = template.Library()

@register.simple_tag
@register.filter
def is_internet_sales_manager(user):
    if user.is_superuser:
        return True
    return user.get_profile().allow_internet_operate
