from B2SUtils.base_actor import as_list
from B2SUtils.base_actor import BaseActor


class ActorRegistration(BaseActor):
    attrs_map = {"type": '@type',
                 "value": "#text"}

class ActorAddress(BaseActor):
    attrs_map = {'addr': 'addr',
                 'zip': 'zip',
                 'city': 'city',
                 'country': 'country'}

class ActorSeller(BaseActor):
    attrs_map = {'name': 'name',
                 'img': 'img'}

    @property
    def registrations(self):
        types = as_list(self.data.get('id'))
        regs = {}
        for type_ in types:
            act = ActorRegistration(data=type_)
            regs[act.type] = act
        return regs

    @property
    def address(self):
        return ActorAddress(data=self.data.get('address'))


class ActorBuyer(BaseActor):
    attrs_map = {'name': 'name'}

    @property
    def address(self):
        return ActorAddress(data=self.data.get('address'))


class ActorPrice(BaseActor):
    attrs_map = {'original': '@original',
                 'value': '#text'}


class ActorSubItem(BaseActor):
    attrs_map = {'desc': 'desc',
                 'qty': 'qty'}


class ActorDetail(BaseActor):
    @property
    def subitem(self):
        subitems = as_list(self.data.get('subitem'))
        return [ActorSubItem(data=item) for item in subitems]


class ActorItem(BaseActor):
    @property
    def desc(self):
        return self.data.get('desc')

    @property
    def subtotal(self):
        return self.data.get('subtotal')

    @property
    def qty(self):
        return self.data.get('qty')

    @property
    def subtotal(self):
        return self.data.get('subtotal')

    @property
    def detail(self):
        detail = self.data.get('detail')
        if detail:
            return ActorDetail(data=detail)

class ActorTax(BaseActor):
    attrs_map = {'name': '@name',
                 'amount': '@amount',
                 'value': '@text'}

class ActorShipping(BaseActor):
    attrs_map = {'desc': 'desc',
                 'postage': 'postage',
                 'handling': 'handling',
                 'subtotal': 'subtotal',
                 'premium': 'premium',
                 'period': 'period'}

    @property
    def tax(self):
        taxes = as_list(self.data.get('tax'))
        return [ActorTax(data=item) for item in taxes]

class ActorTotal(BaseActor):
    attrs_map = {'gross': '@gross',
                 'tax': '@tax',
                 'value': '#text'}


class ActorPayment(BaseActor):
    attrs_map = {'period': 'period',
                 'penalty': 'penalty',
                 'instructions': 'instructions'}

class ActorInvoice(BaseActor):
    attrs_map = {'number': '@number',
                 'currency': '@currency',
                 'date': '@date'
                 }

    @property
    def seller(self):
        return ActorSeller(data=self.data.get('seller'))

    @property
    def buyer(self):
        return ActorBuyer(data=self.data.get('buyer'))

    @property
    def items(self):
        items = as_list(self.data.get('item'))
        return [ActorItem(data=item) for item in items]

    @property
    def shipping(self):
        shipping = self.data.get('shipping')
        if shipping:
            return ActorShipping(data=shipping)

    @property
    def total(self):
        return ActorTotal(data=self.data.get('total'))

    @property
    def payment(self):
        return ActorPayment(data=self.data.get('payment'))

class ActorInvoices(BaseActor):
    @property
    def invoices(self):
        invoices = as_list(self.data.get('invoice'))
        return [ActorInvoice(data=item) for item in invoices]

