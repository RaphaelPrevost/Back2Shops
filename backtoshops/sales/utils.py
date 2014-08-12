from attributes.models import BrandAttribute
from sales.models import TypeAttributePrice

def get_sale_orig_price(sale, type_attribute_id):
    if int(type_attribute_id) == 0:
        return sale.product.normal_price
    else:
        attr_price = TypeAttributePrice.objects.get(
            sale=sale,
            type_attribute_id=type_attribute_id)
        return attr_price.type_attribute_price

def get_sale_discounted_price(sale,
                            type_attribute_price=None,
                            orig_price=None):
    if orig_price is None:
        orig_price = get_sale_orig_price(sale, type_attribute_price)
    if sale.product.discount:
        if sale.product.discount_type == 'percentage':
            return orig_price * (1 - sale.product.discount / 100.0)
        else:
            return orig_price - sale.product.discount
    else:
        return orig_price

def get_sale_premium(price, id_variant):
    premium = 0
    if id_variant:
        variant = BrandAttribute.objects.get(pk=id_variant)
        if variant.premium_type and variant.premium_amount:
            if variant.premium_type == 'fixed':
                premium = variant.premium_amount
            elif variant.premium_type == 'percentage':
                premium = price * variant.premium_amount/100
    return premium

