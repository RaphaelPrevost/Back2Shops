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
from django.db.models import Q
from django.http import HttpResponse
from taxes.models import Rate


def get_rates(request, *args, **kwargs):
    rates_list = []
    region_id = kwargs.get('rid', None)
    rates = Rate.objects.filter(region_id=region_id)

    province_name = request.GET.get('pname', None)
    if province_name:
        rates = rates.filter(
            Q(province='') | Q(province=province_name)
        )
    else:
        rates = rates.filter(province='')

    shipping_to_region_id = request.GET.get('srid', None)
    if shipping_to_region_id:
        rates = rates.filter(
            Q(shipping_to_region_id__isnull=True) |
            Q(shipping_to_region_id=shipping_to_region_id)
        )
    else:
        rates = rates.filter(shipping_to_region_id__isnull=True)

    shipping_to_province_name = request.GET.get('spname', None)
    if shipping_to_province_name:
        rates = rates.filter(
            Q(shipping_to_province='') |
            Q(shipping_to_province=shipping_to_province_name)
        )
    else:
        rates = rates.filter(shipping_to_province='')

    for rate in rates:
        rates_list.append({'label': str(rate), 'value': rate.id})
    return HttpResponse(json.dumps(rates_list), mimetype='application/json')
