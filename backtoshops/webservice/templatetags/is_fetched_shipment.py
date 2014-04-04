from django import template

register = template.Library()

@register.simple_tag
@register.filter
def is_fetched_shipment(status):
    return status and status.lower() == 'fetched'
