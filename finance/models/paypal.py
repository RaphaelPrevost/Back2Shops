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


import datetime
from common.db_utils import update_or_create_trans


def update_or_create_trans_paypal(conn, data):
    values = {
        'id_internal_trans': data['id_trans'],
        'txn_id': data['txn_id'],
        'tax': data['tax'],
        'payment_status': data['payment_status'],
        'payer_id': data['payer_id'],
        'receiver_id': data['receiver_id'],
        'mc_fee': data['mc_fee'],
        'mc_currency': data['mc_currency'],
        'mc_gross': data['mc_gross'],
        'update_time': datetime.datetime.now()
    }

    return update_or_create_trans(conn, 'trans_paypal', data, values,
                                  {'txn_id': data['txn_id']},
                                  data['payment_status'])
