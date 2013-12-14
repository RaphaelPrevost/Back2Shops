import logging
from django import template
from django.core.exceptions import ObjectDoesNotExist
from sales.models import ProductCurrency

register = template.Library()

@register.simple_tag
def get_cur_name(cur_id):
    try:
        cur = ProductCurrency.objects.get(pk=cur_id)
        return cur.code
    except ObjectDoesNotExist:
        logging.warn('No currency for cur_id: %s' % cur_id)
    return ''
