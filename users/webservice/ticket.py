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

import settings
import cgi
import gevent
from datetime import datetime, timedelta

from B2SProtocol.constants import RESP_RESULT
from B2SUtils import db_utils
from B2SUtils.common import parse_ts
from B2SUtils.errors import ValidationError
from common.constants import TICKET_FEEDBACK
from common.constants import TICKET_PRIORITY
from common.utils import get_user_info
from common.utils import push_ticket_event
from webservice.base import BaseJsonResource


class BaseTicketPostResource(BaseJsonResource):

    def _on_post(self, req, resp, conn, **kwargs):
        values = self._get_valid_params()
        ticket_id = self._save_ticket(conn, values)
        if values['parent_id'] == '0':
            self._update_ticket(conn, ticket_id)
        else:
            self._update_parent_ticket(conn, values['parent_id'])
            gevent.spawn(push_ticket_event,
                         email=self.get_user_email(values.get('fo_author')
                                                or values.get('fo_recipient')),
                         service_email=settings.SERVICE_EMAIL,
                         id_brand=values['id_brand'])
        return {"res": RESP_RESULT.S,
                "err": "",
                "id": ticket_id}

    def _save_ticket(self, conn, values):
        ticket_id = db_utils.insert(conn, "ticket", values=values, returning='id')[0]

        # attachment
        form_params = cgi.parse_qs(self.request.query_string)
        for _id in form_params.get('attachment', []):
            db_utils.update(conn, "ticket_attachment",
                            values={'id_ticket': ticket_id},
                            where={'id': _id})
        return ticket_id

    def _update_ticket(self, conn, ticket_id):
        db_utils.update(conn, "ticket",
                        values={'thread_id': ticket_id},
                        where={'id': ticket_id})

    def _update_parent_ticket(self, conn, parent_id):
        db_utils.update(conn, "ticket",
                        values={'replied': True, 'locked': False},
                        where={'id': parent_id})

    def _get_valid_params(self):
        values = {'priority': TICKET_PRIORITY.NORMAL,
                  'id_brand': self.request.get_param('id_brand'),
                  'created': datetime.utcnow()}
        self._check_subject(values)
        self._check_message(values)
        self._check_author(values)
        self._check_parent_id(values)
        self._check_id_order(values)
        self._check_id_shipment(values)
        return values

    def _check_subject(self, values):
        values['subject'] = self._check_param_existing('subject')

    def _check_message(self, values):
        values['message'] = self._check_param_existing('message')

    def _check_author(self, values):
        pass

    def _check_parent_id(self, values):
        parent_id = self.request.get_param('parent_id')
        if parent_id and parent_id != '0':
            row = self._check_param_db_existing('parent_id', 'ticket',
                        ("id", "id_brand", "fo_author", "bo_author", "thread_id"))
            values['parent_id'] = row[0]
            values['id_brand'] = row[1]
            values['fo_recipient'] = row[2]
            values['bo_recipient'] = row[3]
            values['thread_id'] = row[4]
        else:
            values['parent_id'] = '0'

    def _check_id_order(self, values):
        id_order = self.request.get_param('id_order')
        if id_order:
            row = self._check_param_db_existing('id_order', 'orders')
            values['id_order'] = row[0]

    def _check_id_shipment(self, values):
        id_shipment = self.request.get_param('id_shipment')
        if id_shipment:
            row = self._check_param_db_existing('id_shipment', 'shipments')
            values['id_shipment'] = row[0]

    def _check_param_existing(self, fname):
        fvalue = self.request.get_param(fname)
        if not fvalue:
            raise ValidationError('INVALID_PARAM_%s' % fname.upper())
        return fvalue

    def _check_param_db_existing(self, fname, table, fields=None):
        if not fields:
            fields = ("id",)
        fvalue = self.request.get_param(fname)
        result = db_utils.select(self.conn, table,
                                 columns=fields,
                                 where={'id': fvalue})
        if len(result) == 0:
            raise ValidationError('INVALID_PARAM_%s' % fname.upper())
        return result[0]

    def get_user_email(self, id_user):
        row = db_utils.select(self.conn, 'users',
                              columns=('email',),
                              where={'id': id_user})[0]
        return row[0]

class TicketPostResource(BaseTicketPostResource):
    encrypt = True

    def _check_author(self, values):
        values['bo_author'] = self._check_param_existing('author')

class TicketPost4FUserResource(BaseTicketPostResource):
    login_required = {'get': True, 'post': True}

    def _check_author(self, values):
        values['fo_author'] = self.users_id


class BaseTicketListResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        sql = """select id from ticket
            where exists (
                select 1 from ticket as inner_ticket
                where inner_ticket.thread_id = ticket.id
                %(filter_sql)s
            )
            %(sort_sql)s %(page_sql)s
        """
        params = []
        filter_sql = []
        self._filter(req, filter_sql, params)
        sort_sql = []
        self._sort(req, sort_sql, params)
        page_sql = []
        self._paginate(req, page_sql, params)

        threads = db_utils.query(self.conn,
                sql % {'filter_sql': ''.join(filter_sql),
                       'sort_sql': ''.join(sort_sql),
                       'page_sql': ''.join(page_sql)},
                params)
        thread_ids = [t[0] for t in threads]

        return self.get_threads_details(thread_ids)

    def get_threads_details(self, thread_ids):
        if not thread_ids:
            return []

        columns = ("id", "thread_id", "subject", "message",
                   "priority", "feedback", "id_order", "id_shipment",
                   "fo_author", "bo_author", "created")
        sql = ("select %s from ticket"
               " where thread_id in (%s)"
               " order by thread_id, created"
               % (",".join(columns),
                  ",".join(map(str, thread_ids))))
        rows = db_utils.query(self.conn, sql)
        thread_dict = {}
        cached_user_dict = {}
        for row in rows:
            row_dict = dict(zip(columns, row))
            row_dict['attachments'] = self.get_attachments_info(row_dict['id'])
            if row_dict['fo_author']:
                if row_dict['fo_author'] not in cached_user_dict:
                    cached_user_dict[row_dict['fo_author']] = \
                            get_user_info(self.conn, row_dict['fo_author'])
                extra_user_info = cached_user_dict[row_dict['fo_author']]
                row_dict.update(extra_user_info)

            if row_dict['thread_id'] not in thread_dict:
                thread_dict[row_dict['thread_id']] = []
            thread_dict[row_dict['thread_id']].append(row_dict)
        return [thread_dict.get(thread_id, []) for thread_id in thread_ids]

    def get_attachments_info(self, ticket_id):
        rows = db_utils.select(self.conn, 'ticket_attachment',
                               columns=('id', ),
                               where={'id': ticket_id})
        return [{'id': r[0]} for r in rows]

    def _filter(self, req, sql, params):
        pass

    def _sort(self, req, sql, params):
        sort = req.get_param('sort') or '-time'
        if sort:
            if sort[1:] == 'time':
                sql.append(" order by created ")
            elif sort[1:] == 'prio':
                sql.append(" order by priority ")
            else:
                raise ValidationError('INVALID_PARAM_SORT')
            if sort[0] not in ('+', '-'):
                raise ValidationError('INVALID_PARAM_SORT')
            sql.append(("desc" if sort[0] == '-' else "asc"))

    def _paginate(self, req, sql, params):
        page = req.get_param('page') or '0'
        limit = req.get_param('limit') or '10'
        if not limit or not limit.isdigit() or not page or not page.isdigit():
            raise ValidationError('INVALID_REQUEST')
        offset = int(page) * int(limit)
        limit = int(limit) + 1

        sql.append(" limit %s offset %s")
        params.append(limit)
        params.append(offset)

    def _filter_brand(self, req, sql, params):
        id_brand = req.get_param('id_brand')
        if id_brand:
            sql.append(" and id_brand=%s")
            params.append(id_brand)

    def _filter_user(self, req, sql, params):
        id_user = req.get_param('id_user')
        if id_user:
            sql.append(" and (fo_author=%s or fo_recipient=%s)")
            params.append(id_user)

    def _filter_bo_user(self, req, sql, params):
        id_bo_user = req.get_param('id_bo_user')
        if id_bo_user:
            sql.append(" and (bo_author=%s or bo_recipient=%s)")
            params.append(id_bo_user)

    def _filter_order(self, req, sql, params):
        id_order = req.get_param('id_order')
        if id_order:
            sql.append(" and id_order=%s")
            params.append(id_order)

    def _filter_shipment(self, req, sql, params):
        id_shipment = req.get_param('id_shipment')
        if id_shipment:
            sql.append(" and id_shipment=%s")
            params.append(id_shipment)

    def _filter_new(self, req, sql, params):
        new = req.get_param('new') in ('true', 'True')
        if new:
            sql.append(" and parent_id is null")

    def _filter_parent(self, req, sql, params):
        parent_id = req.get_param('parent_id')
        if parent_id:
            sql.append(" and parent_id=%s")
            params.append(parent_id)

    def _filter_escalation(self, req, sql, params):
        escalation = req.get_param('escalation') in ('True', 'true')
        if escalation:
            sql.append(" and escalation is True")

class TicketListResource(BaseTicketListResource):
    encrypt = True

    def _filter(self, req, sql, params):
        self._filter_brand(req, sql, params)
        self._filter_user(req, sql, params)
        self._filter_bo_user(req, sql, params)
        self._filter_order(req, sql, params)
        self._filter_shipment(req, sql, params)
        self._filter_new(req, sql, params)
        self._filter_parent(req, sql, params)
        self._filter_escalation(req, sql, params)

class TicketList4FUserResource(BaseTicketListResource):
    login_required = {'get': True, 'post': True}

    def _filter(self, req, sql, params):
        self._filter_brand(req, sql, params)
        self._filter_user(req, sql, params)
        self._filter_order(req, sql, params)
        self._filter_shipment(req, sql, params)
        self._filter_parent(req, sql, params)

    def _filter_user(self, req, sql, params):
        sql.append(" and (fo_author=%s or fo_recipient=%s)")
        params.append(self.users_id)
        params.append(self.users_id)


class TicketRateResource(BaseJsonResource):
    def _on_post(self, req, resp, conn, **kwargs):
        ticket_id = req.get_param('ticket_id')
        useful = req.get_param('useful') in ('True', 'true')
        feedback = TICKET_FEEDBACK.USEFUL if useful else TICKET_FEEDBACK.USELESS


        rows = db_utils.select(self.conn, 'ticket',
                               columns=('parent_id', 'fo_recipient'),
                               where={'id': ticket_id},
                               limit=1)

        if rows and len(rows) == 1 \
                and rows[0][0] != 0 and rows[0][1] is not None:
            db_utils.update(conn, "ticket",
                            values={'feedback': feedback},
                            where={'id': ticket_id})
        else:
            raise ValidationError('INVALID_PARAM_TICKET_ID')

        return {"res": RESP_RESULT.S,
                "err": ""}


class TicketPriorityResource(BaseJsonResource):
    encrypt = True

    def _on_post(self, req, resp, conn, **kwargs):
        ticket_id = req.get_param('ticket_id')
        priority = req.get_param('priority')
        escalation = req.get_param('escalation')

        update_values = {}
        if priority:
            if priority.isdigit() and int(priority) not in TICKET_PRIORITY.toDict().values():
                raise ValidationError('INVALID_PARAM_PRIORITY')
            update_values.update({'priority': priority})

        if escalation:
            escalation = req.get_param('escalation') in ('True', 'true')
            update_values.update({'escalation': escalation})
            if escalation:
                update_values.update({'escalation_time': datetime.utcnow()})

        rows = db_utils.select(self.conn, 'ticket',
                               columns=('id',),
                               where={'id': ticket_id},
                               limit=1)
        if not rows or len(rows) == 0:
            raise ValidationError('INVALID_PARAM_TICKET_ID')

        db_utils.update(conn, "ticket",
                        values=update_values,
                        where={'id': ticket_id})

        return {"res": RESP_RESULT.S,
                "err": ""}


class TicketLockResource(BaseJsonResource):
    encrypt = True

    def _on_post(self, req, resp, conn, **kwargs):
        ticket_id = req.get_param('ticket_id')
        rows = db_utils.select(self.conn, 'ticket',
                               columns=('locked', 'lock_time'),
                               where={'id': ticket_id},
                               limit=1)
        if not rows or len(rows) == 0:
            raise ValidationError('INVALID_PARAM_TICKET_ID')

        row = rows[0]
        if not row[0] or self._lock_expired(row[1]):
            db_utils.update(conn, "ticket",
                            values={'locked': True,
                                    'lock_time': datetime.utcnow()},
                            where={'id': ticket_id})
        else:
            raise ValidationError('TICKET_LOCKED')

        return {"res": RESP_RESULT.S,
                "err": ""}

    def _lock_expired(self, lock_time):
        return parse_ts(lock_time) + timedelta(seconds=15*60) \
               < datetime.utcnow()


class TicketRelResource(BaseJsonResource):
    encrypt = True

    def _on_get(self, req, resp, conn, **kwargs):
        id_order = req.get_param('id_order')
        id_shipment = req.get_param('id_shipment')
        sql = "select id from ticket where False"
        params = []
        if id_order:
            sql += " or id_order=%s"
            params.append(id_order)
        if id_shipment:
            sql += " or id_shipment=%s"
            params.append(id_shipment)

        rows = db_utils.query(self.conn, sql, params)
        if rows and len(rows) > 0:
            tickets = [row[0] for row in rows]
        else:
            tickets = []
        return {"res": RESP_RESULT.S,
                "err": "",
                "tickets": tickets}


