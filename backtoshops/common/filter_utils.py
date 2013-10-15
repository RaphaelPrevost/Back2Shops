from django.db.models import Q

DJComp_map = {
    '>': '__gt',
    '<': '__lt',
    '>=': '__gte',
    '<=': '__lte',
    '=': '',
    '!=': ''
}

class FilterComparisonErr(Exception):
    pass

class FilterOperatorErr(Exception):
    pass

class FilterFieldErr(Exception):
    pass

class SortFieldErr(Exception):
    pass

class Filter:
    field = None
    name = None
    def __init__(self, operator, comp, value, pre_q=None):
        self.comp = comp
        self.value = value
        self.operator = operator.upper()
        self.pre_q = pre_q

    @property
    def condition(self):
        return self.name + DJComp_map[self.comp]

    @property
    def _allowed_comp(self):
        return ()

    @property
    def _allowed_operator(self):
        return ('AND', 'OR')

    def toQ(self):
        if self.comp not in self._allowed_comp:
            raise FilterComparisonErr('Not allowed comparison %s' % self.comp)

        if self.pre_q and self.operator not in self._allowed_operator:
            raise FilterOperatorErr('Not allowed operator %s' % self.operator)

        q = Q(**{self.condition: self.value})
        if self.comp == '!=':
            q = ~q

        if self.pre_q:
            return (self.pre_q & q
                    if self.operator == 'AND' else self.pre_q | q)
        else:
            return q

class AllComparisonFilter(Filter):
    @property
    def _allowed_comp(self):
        return tuple(DJComp_map.keys())

class ValueFilter(Filter):
    @property
    def _allowed_comp(self):
        return ('=', '!=')

class ProductPriceFilter(AllComparisonFilter):
    field = 'price'
    name = 'product__normal_price'

class BrandFilter(ValueFilter):
    field = 'brand'
    name = 'mother_brand'

class ProductTypeFilter(ValueFilter):
    field = 'type'
    name = 'product__type'

class ProductAttributeFilter(ValueFilter):
    field = 'attribute'
    name = 'product__brand_attributes'

class ShopsFilter(ValueFilter):
    field = 'shops'
    name = 'shops'

def get_filter(name):
    filters = {
        ProductPriceFilter.field: ProductPriceFilter,
        BrandFilter.field: BrandFilter,
        ProductTypeFilter.field: ProductTypeFilter,
        ProductAttributeFilter.field: ProductAttributeFilter,
        ShopsFilter.field: ShopsFilter
    }

    if name not in filters.keys():
        raise FilterFieldErr('No such filter field supported: %s' % name)

    return filters[name]

def get_order_by(name, order):
    orders = {
        'name': 'product__name',
        'price': 'product__normal_price',
        'shop': 'shops',
        'attribute': 'max__product__brand_attributes'
    }

    if name not in orders.keys():
        raise SortFieldErr('No such sort field supported %s' % name)

    sign = '-' if order.upper() == 'DESC' else ''

    return sign + orders[name]

