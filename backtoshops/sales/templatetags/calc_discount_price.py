import logging
from django import template

register = template.Library()

@register.simple_tag
def calc_discount_price(discount_type, discount, base_price):
    try:
        discount = float(discount)
        base_price = float(base_price)
        if discount_type == "percentage":
            tmp = base_price - (base_price * (discount / 100))
            return round(int(tmp * 100) + (int(tmp * 1000 % 10) > 4 and 1 or 0)) / 100
        else:
            return base_price - discount
    except Exception, e:
        logging.warn('Error happened when calculating discount price, '
                     'discount_type: %s, discount: %s, base_price: %s, '
                     'error: %s', discount_type, discount, base_price, e)
    return None

@register.simple_tag
def calc_price_after_tax(price, tax_rate):
    tmp = price + float(price * tax_rate / 100.0)
    return round(int(tmp * 100) + (int(tmp * 1000 % 10) > 4 and 1 or 0)) / 100

@register.simple_tag
def calc_discount_price_after_tax(discount_type, discount, base_price, tax_rate):
    price = calc_discount_price(discount_type, discount, base_price)
    return calc_price_after_tax(price, tax_rate)

