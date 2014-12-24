# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


import ujson
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

    @property
    def tax(self):
        taxes = as_list(self.data.get('tax'))
        return [ActorTax(data=item) for item in taxes]


class ActorTax(BaseActor):
    attrs_map = {'name': '@name',
                 'amount': '@amount',
                 'value': '@text',
                 'show': '@show'}

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
    def items_json(self):
        items = as_list(self.data.get('item'))
        return ujson.dumps(items)

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

