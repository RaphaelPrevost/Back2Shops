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


from django.db import models
from django.utils.translation import ugettext_lazy as _
from shippings.models import Carrier, Service


class Shipping(models.Model):
    addr_orig = models.CharField(verbose_name=_("Origin Address"), max_length=128)
    addr_dest = models.CharField(verbose_name=_("Destination Address"), max_length=128)
    weight = models.FloatField(blank=True, null=True)
    carrier = models.ForeignKey(Carrier, verbose_name=_('Carrier'), blank=True, null=True)
    service = models.ForeignKey(Service, verbose_name=_('Service'), blank=True, null=True)
    handling_fee = models.DecimalField(verbose_name=_('Handling Fees'),
                                       max_digits=10,
                                       decimal_places=2,
                                       blank=True,
                                       null=True)
    ship_and_handling_fee = models.DecimalField(
                                       verbose_name=_('Shipping & Handling Fee'),
                                       max_digits=10,
                                       decimal_places=2,
                                       blank=True,
                                       null=True)
    total_fee = models.DecimalField(verbose_name=_('Fee'),
                                    max_digits=10,
                                    decimal_places=2,
                                    blank=True,
                                    null=True)
    shipment = models.IntegerField(verbose_name='Order',
                                   blank=False,
                                   null=False)

    def __unicode__(self):
        return str(self.order)
