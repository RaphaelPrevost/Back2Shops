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


import datetime
import sys
import ujson
import unittest
sys.path.append('.')
import settings
from common.constants import TICKET_FEEDBACK
from common.test_utils import BaseTestCase
from common.utils import generate_random_str
from B2SProtocol.constants import RESP_RESULT
from B2SUtils import db_utils

class TestUserAuth(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.email = "%s@example.com" % generate_random_str()
        self.password = generate_random_str()
        self.register(self.email, self.password)


    def test_post_ticket(self):
        self.login(self.email, self.password)
        self.pass_auth_verification(self.email)

        values = {
            "id_brand": "1",
            "subject": "how to find the most expensive dollar ?",
            "message": "see subject",
        }
        resp_data = self._post_ticket(values)
        self.assertEquals(resp_data['res'], RESP_RESULT.S)
        t1_id = resp_data['id']

        values = {
            "id_brand": "1",
            "parent_id": t1_id,
            "subject": "additional questions",
            "message": "wow",
        }
        resp_data = self._post_ticket(values)
        self.assertEquals(resp_data['res'], RESP_RESULT.S)
        t2_id = resp_data['id']

        values = {
            "id_brand": "1",
            "subject": "another question",
            "message": "wow",
        }
        resp_data = self._post_ticket(values)
        self.assertEquals(resp_data['res'], RESP_RESULT.S)
        t3_id = resp_data['id']

        # ticket list
        resp_data = self._get_ticketlist()
        self.assertEquals(len(resp_data), 2)
        thread1 = resp_data[0]
        thread2 = resp_data[1]
        self.assertEquals(len(thread1), 1)
        self.assertEquals(thread1[0]['id'], t3_id)
        self.assertEquals(thread1[0]['feedback'], None)
        self.assertEquals(len(thread2), 2)
        self.assertEquals(thread2[0]['id'], t1_id)
        self.assertEquals(thread2[0]['feedback'], None)
        self.assertEquals(thread2[1]['id'], t2_id)
        self.assertEquals(thread2[1]['feedback'], None)

        # rate
        resp_data = self._rate_ticket(t1_id, True)
        self.assertEquals(resp_data['res'], RESP_RESULT.F)
        resp_data = self._rate_ticket(t2_id, True)
        self.assertEquals(resp_data['res'], RESP_RESULT.S)
        resp_data = self._get_ticketlist()
        self.assertEquals(len(resp_data), 2)
        thread1 = resp_data[0]
        thread2 = resp_data[1]
        self.assertEquals(len(thread2), 2)
        self.assertEquals(thread2[1]['id'], t2_id)
        self.assertEquals(thread2[1]['feedback'], TICKET_FEEDBACK.USEFUL)


    def _post_ticket(self, values):
        resp = self.b._access("webservice/1.0/pub/tickets/post", values)
        return ujson.loads(resp.get_data())

    def _get_ticketlist(self):
        resp = self.b._access("webservice/1.0/pub/tickets/list")
        return ujson.loads(resp.get_data())

    def _rate_ticket(self, ticket_id, useful):
        resp = self.b._access("webservice/1.0/pub/tickets/rate",
                              {'ticket_id': ticket_id, 'useful': useful})
        return ujson.loads(resp.get_data())


if __name__ == '__main__':
    unittest.main()
