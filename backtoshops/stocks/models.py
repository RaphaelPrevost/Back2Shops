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


from django.db import models
from attributes.models import BrandAttribute, CommonAttribute
from sales.models import Sale
from shops.models import Shop

class ProductStock(models.Model):
    sale = models.ForeignKey(Sale, related_name="detailed_stock", on_delete=models.CASCADE)
    brand_attribute = models.ForeignKey(BrandAttribute, null=True, blank=True)
    common_attribute = models.ForeignKey(CommonAttribute, null=True, blank=True)
    shop = models.ForeignKey(Shop, null=True, blank=True)
    stock = models.IntegerField(default=0)
    rest_stock = models.IntegerField(default=0)
    alert = models.BooleanField(default=False)

    def __unicode__(self):
        return '%d:%d:%s' % (self.stock, self.rest_stock, self.sale)

