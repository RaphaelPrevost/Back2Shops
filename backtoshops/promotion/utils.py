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


import logging
from promotion.models import SalesInGroup
from promotion.models import TypesInGroup
from sales.models import STOCK_TYPE_DETAILED

def save_sale_promotion_handler(sale):
    cur_records = SalesInGroup.objects.filter(sale=sale)
    cur_groups = [item.group for item in cur_records]
    local_market = sale.type_stock == STOCK_TYPE_DETAILED
    for item in cur_records:
        # check whether sale's type in group selected types,
        # if no, delete the sale's record from the group
        if sale.product.type not in item.group.types.all():
            orig_types = [str(t.pk) for t in item.group.types.all()]
            group_record = '-'.join([str(item.group_id), str(item.sale_id)])
            item.delete()
            logging.info("%s group deleted since sale's type "
                         "have been changed: "
                         "new type: %s "
                         "group selected types: %s",
                         group_record,
                         sale.product.type.pk,
                         ', '.join(orig_types))

        # check whether group's shop still in sale's shops, if no delete
        # the sale record from the group
        sale_shops = sale.shops.all()
        group_shop = item.group.shop
        # for local market sale, check group shop still is in sale's shops.
        need_delete = (local_market and
                       group_shop not in sale_shops)
        # check whether sale's market changed from global to local,
        # or local to global.
        need_delete = (need_delete or
                       (group_shop and not local_market) or
                       (not group_shop and local_market))

        if need_delete:
            sale_shops = [str(s.pk) for s in sale.shops.all()]
            group_record = '-'.join([str(item.group_id), str(item.sale_id)])
            item.delete()
            logging.info("%s group deleted since sale's shops "
                         "have been changed: "
                         "new shops: %s "
                         "group selected shop: %s",
                         group_record,
                         local_market and ', '.join(sale_shops) or "global market",
                         group_shop)
    if local_market:
        matched_type_records = TypesInGroup.objects.filter(
            type=sale.product.type,
            group__brand=sale.mother_brand,
            group__shop__in=sale.shops.all())
    else:
        matched_type_records = TypesInGroup.objects.filter(
            type=sale.product.type,
            group__brand=sale.mother_brand,
            group__shop__isnull=True)

    matched_group = [t.group for t in matched_type_records]

    ext_groups = set(matched_group) - set(cur_groups)
    for group in ext_groups:
        SalesInGroup.objects.create(
            group=group,
            sale=sale)
        logging.info("sale %s automatically added into group %s",
                     sale.pk, group.pk)

def drop_sale_promotion_handler(sale):
    r = SalesInGroup.objects.filter(sale=sale)
    group_record = []
    for item in r:
        group_record.append('-'.join([str(item.group_id),
                                      str(item.sale_id)]))
    r.delete()
    if group_record:
        logging.info("sales in group %s have been deleted "
                     "since sale has been deleted", ', '.join(group_record))
