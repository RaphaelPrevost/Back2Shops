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

from accounts.models import Brand
from sales.models import Sale
from shops.models import Shop
from attributes.models import BrandAttribute


class Visitors(models.Model):
    sid = models.CharField(max_length=36, primary_key=True)
    users_id = models.IntegerField(blank=True, null=True)
    visit_time = models.DateTimeField(blank=False, null=False)

    def __unicode__(self):
        return str(self.sid) + '-' + str(self.users_id)

class Incomes(models.Model):
    sale = models.ForeignKey(Sale)
    shop = models.ForeignKey(Shop)
    variant = models.ForeignKey(BrandAttribute)
    price = models.FloatField(null=False, blank=False)
    quantity = models.IntegerField(null=False, blank=False)
    users_id = models.IntegerField(null=False, blank=False)
    up_time = models.DateTimeField(null=False, blank=False)

class Orders(models.Model):
    users_id = models.IntegerField()
    order_id = models.IntegerField()
    brand = models.ForeignKey(Brand)
    shop = models.ForeignKey(Shop, null=True, blank=True)
    pending_date = models.DateField(null=True, blank=True)
    waiting_payment_date = models.DateField(null=True, blank=True)
    waiting_shipping_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)

class BoughtHistory(models.Model):
    sale = models.ForeignKey(Sale, null=False, blank=False)
    users = models.TextField(null=False, blank=False)
