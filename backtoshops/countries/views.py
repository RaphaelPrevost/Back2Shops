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


import json
from django.http import HttpResponse
from countries.models import CaProvince
from countries.models import CnProvince
from countries.models import CountryXCurrency
from countries.models import UsState
from sales.models import ProductCurrency


COUNTRY_STATE_MODEL_MAP = {
    'US': UsState,
    'CA': CaProvince,
    'CN': CnProvince,
}


def get_country_states(request, *args, **kwargs):
    states_list = []
    country_iso = kwargs.get('cid', None)
    if country_iso:
        state_model = COUNTRY_STATE_MODEL_MAP.get(country_iso, None)
        if state_model:
            states = state_model.objects.all()
            for state in states:
                states_list.append({'label': state.name, 'value': state.abbrev})
    return HttpResponse(json.dumps(states_list), mimetype='application/json')

def get_country_x_currency(request, *args, **kwargs):
    product_currencies = ProductCurrency.objects.all().values_list('code',
                                                                   flat=True)
    mapping = {}
    for country, currency in CountryXCurrency.objects.all().values_list(
                                                'country_id', 'currency'):
        if currency in product_currencies and country not in mapping:
            mapping[country] = currency
    return HttpResponse(json.dumps(mapping), mimetype='application/json')

