import logging
from django import template
from django.core.exceptions import ObjectDoesNotExist
from attributes.models import CommonAttribute

register = template.Library()

@register.simple_tag
def get_ta_name(type_attribute_id):
    try:
        ta = CommonAttribute.objects.get(pk=type_attribute_id)
        return ta.name
    except ObjectDoesNotExist:
        logging.warn('No item attribute for id: %s' % type_attribute_id)
    return ''
