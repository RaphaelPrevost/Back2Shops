# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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


from B2SUtils.base_actor import as_list
from B2SUtils.base_actor import BaseActor
from B2SProtocol.constants import SHIPMENT_STATUS

st_desc_map = {
    SHIPMENT_STATUS.CONFIRMING: 'CONFIRMING',
    SHIPMENT_STATUS.PACKING: 'PACKING',
    SHIPMENT_STATUS.DELAYED: 'DELAYED',
    SHIPMENT_STATUS.DELIVER: 'DELIVER',
    SHIPMENT_STATUS.DELETED: 'DELETED',
    SHIPMENT_STATUS.FETCHED: 'FETCHED',
}

class ActorService(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'desc': 'desc'}

class ActorCarrier(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}

    @property
    def services(self):
        services_data = as_list(self.data.get('service'))
        return [ActorService(data=service) for service in services_data]

class ActorTracking(BaseActor):
    attrs_map = {'code': 'code',
                 'url': 'url'}


class ActorHandling(BaseActor):
    attrs_map = {'currency': '@currency',
                 'value': '#text'}

class ActorShipping(BaseActor):
    attrs_map = {'currency': '@currency',
                 'value': '#text'}

class ActorFees(BaseActor):
    @property
    def handling(self):
        return ActorHandling(data=self.data.get('handling'))

    @property
    def shipping(self):
        shipping_data = self.data.get('shipping')
        if shipping_data is None:
            return
        return ActorShipping(data=shipping_data)

class ActorDelivery(BaseActor):
    attrs_map = {'status': '@status'}

    @property
    def carriers(self):
        carriers_data = as_list(self.data.get('carrier'))
        return [ActorCarrier(data=carrier) for carrier in carriers_data]

    @property
    def tracking(self):
        tk_data = self.data.get('tracking')
        if tk_data is None:
            return
        return ActorTracking(data=tk_data)

    @property
    def status_desc(self):
        return st_desc_map[int(self.status)]


class ActorAttribute(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}


class ActorType(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}
    @property
    def attribute(self):
        return ActorAttribute(data=self.data.get('attribute'))

class ActorVariant(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}

class ActorWeight(BaseActor):
    attrs_map = {'unit': '@unit',
                 'value': '#text'}

class ActorItem(BaseActor):
    attrs_map = {'sale': '@sale',
                 'name': 'name',
                 'currency': 'currency',
                 'quantity': 'quantity',
                 'external_id': 'external_id',
                 'barcode': 'barcode',
                 'picture': 'picture',
                 'packing_quantity': 'packing_quantity',
                 'remaining_quantity': 'remaining_quantity',
                 'shipping_status': 'shipping_status',
                 'id_order_item': "@id_order_item"}
    @property
    def type(self):
        type_data = self.data.get('type')
        if type_data is None:
            return
        return ActorType(data=type_data)

    @property
    def variant(self):
        variant_data = self.data.get('variant')
        if variant_data is None:
            return
        return ActorVariant(data=variant_data)

    @property
    def weight(self):
        return ActorWeight(data=self.data.get('weight'))


class ActorShipment(BaseActor):
    attrs_map = {'id': '@id',
                 'method': '@method',
                 'brand': '@brand',
                 'shop': '@shop',
                 'tracking_num': "tracking_num",
                 'shipping_date': "shipping_date",
                 'tracking_name': "tracking_name"}

    @property
    def paid_date(self):
        return self.data.get('@paid_date')

    @property
    def delivery(self):
        return ActorDelivery(data=self.data.get('delivery'))

    @property
    def fees(self):
        fees_data = self.data.get('fees')
        if fees_data is None:
            return
        return ActorFees(data=fees_data)

    @property
    def items(self):
        items_data = as_list(self.data.get('item'))
        return [ActorItem(data=item) for item in items_data]

    @property
    def shipping_carrier(self):
        if self.data.get('shipping_carrier'):
            return int(self.data.get('shipping_carrier'))



class ActorShipments(BaseActor):
    attrs_map = {'order_status': "@order_status",
                 'order_create_date': "@order_create_date"}
    @property
    def shipments(self):
        shipments_data = as_list(self.data.get('shipment'))
        return [ActorShipment(data=spm) for spm in shipments_data]
