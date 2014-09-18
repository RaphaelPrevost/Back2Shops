from django import template

register = template.Library()

@register.simple_tag
def get_discount_price(discount_type, discount_value, price):
    if discount_type == 'percentage':
        price = price * (100 - float(discount_value)) / 100
    else:
        price = price - float(discount_value)
    return price

