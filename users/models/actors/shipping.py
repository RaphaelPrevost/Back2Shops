# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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


class ActorTypeAttribute(BaseActor):
    attrs_map = {'id': '@id',
                 'name': '@name'}

class ActorType(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}
    @property
    def attribute(self):
        attribute_data = self.data.get('attribute')
        if attribute_data:
            return ActorTypeAttribute(data=attribute_data)

class ActorWeight(BaseActor):
    attrs_map = {'unit': '@unit',
                 'value': '#text'}

class ActorVariant(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}

class ActorOption(BaseActor):
    attrs_map = {'name': '@name',
                 'value': '@value'}

class ActorOptions(BaseActor):
    @property
    def option_list(self):
        op_list = as_list(self.data.get('option'))
        return [ActorOption(data=item) for item in op_list]

    @property
    def group_shipment(self):
        return self.option_list[0]

    @property
    def local_pickup(self):
        return self.option_list[1]

    @property
    def void_handling(self):
        return self.option_list[2]

    @property
    def free_shipping(self):
        return self.option_list[3]

    @property
    def flat_rate(self):
        return self.option_list[4]

    @property
    def carrier_shipping_rate(self):
        return self.option_list[5]

    @property
    def custom_shipping_rate(self):
        return self.option_list[6]

    @property
    def invoice_shipping_rate(self):
        return self.option_list[7]

class ActorService(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'desc': 'desc'}

class ActorCarrier(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}

    @property
    def services(self):
        service_list = as_list(self.data.get('service'))
        return [ActorService(item) for item in service_list]

class ActorHandling(BaseActor):
    attrs_map = {'currency': '@currency',
                 'value': '#text'}

class ActorFeesShipping(BaseActor):
    attrs_map = {'currency': '@currency',
                 'value': '#text'}

class ActorFees(BaseActor):
    @property
    def handling(self):
        return ActorHandling(data=self.data.get('handling'))

    @property
    def shipping(self):
        shipping_data = self.data.get('shipping')
        if shipping_data:
            return ActorFeesShipping(data=shipping_data)

class ActorSetting(BaseActor):
    attrs_map = {'name': 'name',
                 'for_': '@for'}

    _supported_services = None

    @property
    def type(self):
        type_data = self.data.get("type")
        if type_data:
            return ActorType(data=self.data.get("type"))

    @property
    def variant(self):
        variant_data = self.data.get('variant')
        if variant_data:
            return ActorVariant(data=variant_data)

    @property
    def weight(self):
        return ActorWeight(data=self.data.get('weight'))

    @property
    def options(self):
        return ActorOptions(data=self.data.get('options'))

    @property
    def carriers(self):
        carriers_list = as_list(self.data.get('carrier'))
        return [ActorCarrier(data=item) for item in carriers_list]

    @property
    def fees(self):
        return ActorFees(data=self.data.get('fees'))

    @property
    def supported_services(self):
        if self._supported_services is None:
            self.refresh_supported_services()
        return self._supported_services

    def refresh_supported_services(self):
        if not self.carriers:
            return
        supported_services = {}
        for carrier in self.carriers:
            for service in carrier.services:
                supported_services[service.id] = carrier.id
        self._supported_services = supported_services

class ActorShipping(BaseActor):
    @property
    def settings(self):
        setting_list = as_list(self.data.get('settings'))
        return [ActorSetting(data=item) for item in setting_list]


class ActorCarriers(BaseActor):
    @property
    def carriers(self):
        carriers_list = as_list(self.data.get('carrier'))
        return [ActorCarrier(data=item) for item in carriers_list]
