import logging
from django import template

register = template.Library()

@register.simple_tag
def calc_premium_price(premium_type, premium_amount, price):
    try:
        premium_amount = float(premium_amount)
        price = float(price)
        if premium_type == "percentage":
            tmp = price + (price * (premium_amount / 100))
            return round(tmp * 100 + ((tmp * 1000 % 10 > 4) and 1 or 0)) / 100
        else:
            return price + premium_amount;
    except Exception, e:
        logging.warn('Error happened when calculating premium price, '
                     'premium_type: %s, premium_amount: %s, price: %s, '
                     'error: %s', premium_type, premium_amount, price, e)
    return None
