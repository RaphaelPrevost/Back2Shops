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


import logging
import ujson
import xmltodict
import settings

from StringIO import StringIO
from lxml import etree

from B2SProtocol.constants import FAILURE
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM
from B2SProtocol.constants import SUCCESS
from B2SUtils.errors import ValidationError
from common.email_utils import send_html_email
from common.error import ServerError
from common.utils import invoice_xslt
from common.utils import remote_xml_invoice
from models.actors.invoices import ActorInvoices
from models.actors.shop import CachedShop
from models.invoice import create_invoice
from models.invoice import get_invoice_by_order
from models.invoice import get_invoices_by_shipments
from models.invoice import iv_to_sent_qty
from models.invoice import order_iv_sent_status
from models.order import get_order_status
from models.order import get_order
from models.shipments import get_shipments_by_id
from models.shipments import get_shipments_by_order
from models.shipments import get_shipping_fee
from models.shipments import get_shipping_list
from models.shipments import get_supported_services
from models.user import get_user_dest_addr
from models.user import get_user_email
from models.user import get_user_profile
from webservice.base import BaseJsonResource
from webservice.base import BaseXmlResource


HEADER = """<?xml version="1.0" standalone="no"?>"""
DTD_HEADER = """<!DOCTYPE invoices PUBLIC "-//BACKTOSHOPS//INVOICE" "invoice.dtd">"""
CONTENT_HEADER = """<invoices version="1.0">"""
CONTENT_ROOT = """</invoices>"""

INVOICE_MAIL_SUB = "[Backtoshops]: Invoice"


class BaseInvoiceMixin:
    def get_and_save_invoices(self, conn, req, id_user,
                              id_shipments=None):
        id_order = req.get_param('order')

        if not id_order:
            raise ValidationError("Miss param in request")

        order = get_order(conn, id_order, id_user=id_user)
        if order is None:
            raise ValidationError("Order not exist")

        # address
        id_shipaddr = order['id_shipaddr']
        dest = get_user_dest_addr(conn, id_user, id_shipaddr)
        dest = ujson.dumps(dest)

        # customer
        user = get_user_profile(conn, id_user)

        if id_shipments is not None:
            shipments = get_shipments_by_id(conn, id_shipments)
        else:
            shipments = get_shipments_by_order(conn, id_order)

        invoices = {}
        for sp in shipments:
            invoice_xml = self.get_shipment_invoice(conn, dest, user, sp)
            if invoice_xml is None:
                continue
            invoices[sp['id']] = invoice_xml

        shipments_id = invoices.keys()
        shipments_id.sort()

        content = self.gen_invoices_content(
            [invoices[id_shipment]
             for id_shipment in shipments_id if invoices.get(id_shipment)])
        return content

    def save_invoice(self, conn, id_order, id_shipment,
                     invoice_xml, invoice_actor):
        return create_invoice(conn,
                              id_order,
                              id_shipment,
                              invoice_actor.total.value,
                              invoice_actor.currency,
                              invoice_xml,
                              invoice_actor.number,
                              due_within=invoice_actor.payment.period,
                              shipping_within=invoice_actor.shipping.period,
                              invoice_items=invoice_actor.items_json,
                              )

    def parse_invoices_content(self, xml):
        content = xml[len(HEADER):].strip()
        content = content[len(DTD_HEADER):].strip()
        content = content[len(CONTENT_HEADER):]
        content = content[:-len(CONTENT_ROOT)]
        return content

    def unitary_content(self, content_list):
        content_data = [HEADER, CONTENT_HEADER]
        content_data.extend(content_list)
        content_data.append(CONTENT_ROOT)
        content = '\n'.join(content_data)
        return content


    def gen_invoices_content(self, invoices_xml):
        invoices = []
        for xml in invoices_xml:
            content = self.parse_invoices_content(xml)
            invoices.append(content)

        return invoices

    def get_shipment_invoice(self, conn, dest, user, shipment):
        id_shipment = shipment['id']
        customer = ' '.join([user['first_name'], user['last_name']])

        # get from database
        iv_from_db = get_invoices_by_shipments(conn, [id_shipment])
        if iv_from_db:
            return iv_from_db[0]['invoice_xml']

        # get from remote
        cal_method = shipment['calculation_method']
        id_shop = shipment['id_shop']
        id_brand = shipment['id_brand']
        id_order = shipment['id_order']
        query = {
            'customer': customer,
            'dest': dest,
            'shop': id_shop,
            'brand': id_brand,
            'is_business_account': user.get('is_business_account'),
            'company_name': user.get('company_name') or '',
            'company_position': user.get('company_position') or '',
            'company_tax_id': user.get('company_tax_id') or '',
        }

        if cal_method in [SCM.CARRIER_SHIPPING_RATE,
                          SCM.CUSTOM_SHIPPING_RATE]:
            supported_services = get_supported_services(conn,
                                                        id_shipment)[0]

            id_service = supported_services['id_postage']
            if id_service:
                servs = supported_services['supported_services']
                servs = ujson.loads(servs)
                id_carrier = servs[str(id_service)]
                query['carrier'] = id_carrier
                query['service'] = id_service
            elif shipment['shipping_carrier']:
                pass
            else:
                logging.error("Shipment %s haven't been conf", id_shipment)
                return

        if cal_method in [SCM.CARRIER_SHIPPING_RATE,
                          SCM.CUSTOM_SHIPPING_RATE,
                          SCM.FLAT_RATE,
                          SCM.MANUAL]:
            try:
                fee = get_shipping_fee(conn, id_shipment)
                if fee['shipping_fee'] is not None:
                    query['shipping_fee'] = fee['shipping_fee']
                if fee['handling_fee'] is not None:
                    query['handling_fee'] = fee['handling_fee']
            except AssertionError:
                pass

        query['content'] = self.shipment_content(conn, id_shipment)

        xml_invoice = remote_xml_invoice(query)
        valid = self.validate_invoice(xml_invoice)
        if not valid:
            logging.error("invalidate_invoice_result: %s",
                          xml_invoice, exc_info=True)
            raise ServerError("invalidate invoice result")

        # Save invoice into database
        invoice = xmltodict.parse(xml_invoice)
        actor_invoices = ActorInvoices(data=invoice['invoices'])
        for actor_invoice in actor_invoices.invoices:
            self.save_invoice(conn, id_order, id_shipment,
                              xml_invoice, actor_invoice)

        return xml_invoice

    def shipment_content(self, conn, id_shipment):
        shipping_list = get_shipping_list(conn, id_shipment)

        content = []
        for shipping in shipping_list:
            content.append({"id_item": shipping["id_item"],
                            "id_sale": shipping["id_sale"],
                            "id_variant": shipping["id_variant"],
                            "quantity": shipping["quantity"],
                            "id_price_type": shipping["id_price_type"],
                            "id_type": shipping["id_type"],
                            "name": shipping["name"] or '',
                            "type_name": shipping["type_name"] or '',
                            "external_id": shipping["external_id"] or '',
                            })

        return ujson.dumps(content)

    def validate_invoice(self, xml_invoice):
        with open(settings.INVOICE_VALIDATE_PATH) as f:
            dtd_content = f.read()
            f.close()

        xml_invoice = xml_invoice.strip()

        dtd = etree.DTD(StringIO(dtd_content))
        root = etree.XML(xml_invoice)
        rst = dtd.validate(root)
        if not rst:
            logging.error(dtd.error_log.filter_from_errors())
        return rst

    def invoice_xslt(self, content):
        return invoice_xslt(content, self.language)


class InvoiceResource(BaseXmlResource, BaseInvoiceMixin):
    template = "invoices.xml"
    encrypt = False
    login_required = {'get': False, 'post': True}

    def gen_resp(self, resp, data):
        if data.get('content'):
            try:
                content = data['content']
                content = self.unitary_content(content)
                resp.body = content
                resp.content_type = "application/xml"
            except Exception, e:
                if self.conn:
                    self.conn.rollback()
                return super(InvoiceResource, self).gen_resp(
                    resp, {'error': "Server error"})
            return resp
        else:
            return super(InvoiceResource, self).gen_resp(resp, data)

    def _on_post(self, req, resp, conn, **kwargs):
        content = self.get_and_save_invoices(conn,
                                             req,
                                             self.users_id)
        return {'content': content}

class BaseInvoiceGetResource(BaseJsonResource, BaseInvoiceMixin):
    encrypt = True
    login_required = {'get': False, 'post': False}

    def _get_invoices(self, conn, id_order, id_brand, id_shops):
        try:
            shipments = get_shipments_by_order(conn, id_order)
            invoices = get_invoice_by_order(conn, id_order)
            spm_dict = dict([(spm['id'], spm) for spm in shipments])
            content = []

            for iv in invoices:
                id_shipment = iv['id_shipment']
                spm = spm_dict.get(id_shipment)
                if not spm:
                    continue
                if spm['id_brand'] != id_brand:
                    continue
                if id_shops and spm['id_shop'] not in id_shops:
                    continue

                content.append(
                    {'id': iv['id'],
                     'id_shipment': iv['id_shipment'],
                     'html': self.invoice_xslt(iv['invoice_xml'])})

            order_iv_status = order_iv_sent_status(conn, id_order, id_brand,
                                                   id_shops)
            order_status = get_order_status(conn, id_order)
            to_sent_qty = iv_to_sent_qty(conn, id_order, id_brand, id_shops)
            return {'res': SUCCESS,
                    'iv_sent_status': order_iv_status,
                    'iv_to_sent_qty': to_sent_qty,
                    'order_status': order_status,
                    'content': content}
        except Exception, e:
            conn.rollback()
            logging.error("get_invoice_server_err: %s", str(e), exc_info=True)
            return {'res': FAILURE,
                    'reason': str(e),
                    'err': "SERVER_ERROR"}


class InvoiceGet4FUserResource(BaseInvoiceGetResource):
    encrypt = False
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, conn, **kwargs):
        try:
            id_order = req.get_param('order')
            id_brand = req.get_param('brand')
            if not id_brand or not id_order:
                raise ValidationError("iv_get_req_err: miss params")
        except ValidationError, e:
            logging.error("get_invoice_invalidate: %s", str(e), exc_info=True)
            return {'res': FAILURE, 'err': str(e)}

        return self._get_invoices(conn, id_order, int(id_brand), id_shops=[])


class InvoiceGetResource(BaseInvoiceGetResource):

    def _on_get(self, req, resp, conn, **kwargs):
        try:
            id_order = req.get_param('order')
            id_brand = req.get_param('brand')
            id_shops = req.get_param('shops')
            if not id_brand or not id_shops or not id_order:
                raise ValidationError("iv_get_req_err: miss params")
        except ValidationError, e:
            logging.error("get_invoice_invalidate: %s", str(e), exc_info=True)
            return {'res': FAILURE, 'err': str(e)}

        id_shops = [int(id_shop) for id_shop in ujson.loads(id_shops)]
        return self._get_invoices(conn, id_order, int(id_brand), id_shops)


class InvoiceSendResource(BaseJsonResource, BaseInvoiceMixin):
    encrypt = True
    login_required = {'get': False, 'post': False}

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            params= req.stream.read()
            params = ujson.loads(params)
            req._params.update(params)

            id_order = params.get('order')
            id_shipments = params.get('shipment') or '[]'
            id_brand = params.get('brand')
            id_shops = params.get('shops')

            if not id_brand or not id_shops or not id_order:
                raise ValidationError("iv_send_req_err: miss params")
            id_brand = int(id_brand)
            id_shops = [int(id_shop) for id_shop in ujson.loads(id_shops)]
            id_shipments = [int(id_spm)
                            for id_spm in ujson.loads(id_shipments)]
            orig_id_spms = id_shipments

            shipments = get_shipments_by_order(conn, id_order)
            shipments = dict([(sp['id'], sp) for sp in shipments])
            valid_shipments = shipments.keys()
            order = get_order(conn, id_order)

            if id_shipments:
                invalid_shipments = set(id_shipments) - set(valid_shipments)
                if len(invalid_shipments) > 0:
                    raise ValidationError("shipments %s not belongs to "
                                          "order %s"
                                          % (invalid_shipments, id_order))

                for id_spm in id_shipments:
                    spm_brand = shipments[id_spm]['id_brand']
                    spm_shop = shipments[id_spm]['id_shop']

                    if spm_brand != id_brand:
                        raise ValidationError(
                            "iv_send_req_err: spm brand %s is not "
                            "same with given %s"
                            % (spm_brand, id_brand))
                    if spm_shop not in id_shops:
                        raise ValidationError(
                            "iv_send_req_err: spm shop %s is not "
                            "in given shops %s"
                            % (spm_shop, id_shops))
            else:
                for id_spm, spm in shipments.iteritems():
                    if (spm['id_brand'] == id_brand and
                        spm['id_shop'] in id_shops):
                        id_shipments.append(id_spm)

            self.get_and_save_invoices(conn, req, order['id_user'],
                                       id_shipments=id_shipments)
            order_invoices = get_invoice_by_order(conn, id_order)

            invoices = dict([(oi['id_shipment'], oi) for oi in order_invoices])
            users_mail = get_user_email(conn, order['id_user'])
            if orig_id_spms:
                for id_spm in id_shipments:
                    if invoices.get(id_spm) is None:
                        continue
                    content = invoices[id_spm]['invoice_xml']
                    content_html = self.invoice_xslt(content)
                    send_html_email(users_mail, INVOICE_MAIL_SUB, content_html)
            else:
                content_list = []
                for id_spm in id_shipments:
                    if invoices.get(id_spm) is None:
                        continue
                    content = invoices[id_spm]['invoice_xml']
                    content = self.parse_invoices_content(content)
                    content_list.append(content)
                content = self.unitary_content(content_list)
                content_html = self.invoice_xslt(content)
                send_html_email(users_mail, INVOICE_MAIL_SUB, content_html)

            order_iv_status = order_iv_sent_status(conn, id_order, id_brand,
                                                   id_shops)
            return {'res': SUCCESS,
                    'order_iv_status': order_iv_status}
        except ValidationError, e:
            conn.rollback()
            logging.error("send_invoice_invalidate: %s", str(e), exc_info=True)
            return {'res': FAILURE,
                    'err': str(e)}
        except Exception, e:
            conn.rollback()
            logging.error("send_invoice_server_err: %s", str(e), exc_info=True)
            return {'res': FAILURE,
                    'reason': str(e),
                    'err': "SERVER_ERROR"}
