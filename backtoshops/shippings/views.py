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


from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.base import View

from fouillis.views import ManagerUpperLoginRequiredMixin
from shippings.forms import CustomShippingRateFormModel
from shippings.models import CustomShippingRate


class CustomShippingRateView(ManagerUpperLoginRequiredMixin,
                             View,
                             TemplateResponseMixin):
    template_name = "_ajax_custom_shipping_rates.html"

    def post(self, request):
        try:
            form = CustomShippingRateFormModel(request.POST, request.FILES)
            if form.is_valid():
                self.new_custom_shipping_rate = form.save(commit=False)
                self.new_custom_shipping_rate.seller = \
                    request.user.get_profile().work_for
                self.new_custom_shipping_rate.save()
                messages.success(
                    request,
                    _("The custom shipping rate has been successfully created."
                    ))
                self.custom_shipping_rates = \
                    CustomShippingRate.objects.filter(
                        seller=request.user.get_profile().work_for)
            else:
                self.errors = form.errors
        except Exception as e:
            self.errors = e
        return self.render_to_response(self.__dict__)
