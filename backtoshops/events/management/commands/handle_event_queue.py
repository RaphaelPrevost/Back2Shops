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
import logging
from django.core.management.base import BaseCommand

from B2SUtils.email_utils import send_email
from common.constants import NOTIF_DELIVERY_METHOD
from events.models import EventQueue


class Command(BaseCommand):
    help = "handle event queue"

    def handle(self, *args, **options):
        try:
            to_handle = EventQueue.objects.filter(handled=False).filter(error='').order_by('created')
            for q in to_handle:
                try:
                    event = q.event
                    param_values = json.loads(q.param_values)
                    brand = param_values['brand']
                    for n in event.notifs.get_query_set():
                        if int(brand) == n.mother_brand.id:
                            self._handle_notif(n, param_values)
                    q.handled = True
                    q.save()
                except Exception, e:
                    logging.error("handle_event_queue_err: %s", e, exc_info=True)
                    q.error = str(e)
                    q.save()

        except Exception, e:
            logging.error('handle_event_queue_err: %s', e, exc_info=True)

    def _handle_notif(self, notif, param_values):
        if notif.delivery_method == NOTIF_DELIVERY_METHOD.EMAIL:
            service_email = param_values['service_email']
            email = param_values['email']
            subject = notif.subject % param_values
            content = ("<html><header>%s</header><body>%s</body></html>"
                       % (notif.html_head,
                          notif.html_body or notif.event.predefined_template))
            content = content % param_values
            send_email(service_email, email, subject, content, None)
        else:
            raise Exception('Missing delievery method plugin: %s' % notif.delivery_method)


