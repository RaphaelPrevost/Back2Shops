import logging
import ujson
import xmltodict
import settings

from lxml import etree
from StringIO import StringIO
from common.error import ServerError
from common.utils import remote_xml_invoice
from models.actors.invoices import ActorInvoices
from models.invoice import create_invoice
from models.invoice import get_invoice_by_order
from models.order import get_order
from models.shipments import get_shipments_by_order
from models.shipments import get_shipping_fee
from models.shipments import get_shipping_list
from models.shipments import get_supported_services
from models.user import get_user_dest_addr
from models.user import get_user_profile

from webservice.base import BaseXmlResource

from B2SUtils.errors import ValidationError
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM


HEADER = """<?xml version="1.0" standalone="no"?>"""
DTD_HEADER = """<!DOCTYPE invoices PUBLIC "-//BACKTOSHOPS//INVOICE" "invoice.dtd">"""
CONTENT_HEADER = """<invoices version="1.0">"""
CONTENT_ROOT = """</invoices>"""


class InvoiceResource(BaseXmlResource):
    template = "invoices.xml"
    encrypt = False
    login_required = {'get': False, 'post': True}


    def gen_resp(self, resp, data):
        if data.get('content'):
            try:
                content = data['content']
                content_data = [HEADER, CONTENT_HEADER]
                content_data.extend(content)
                content_data.append(CONTENT_ROOT)
                content = '\n'.join(content_data)
                if settings.INVOICE_XSLT_REQUIRED:
                    resp.body = self.invoice_xslt(content)
                    resp.content_type = "text/html"
                    return resp
                else:
                    resp.body = content
                    resp.content_type = "application/xml"
            except Exception, e:
                return super(InvoiceResource, self).gen_resp(
                    resp, {'error': "Server error"})
            return resp
        else:
            return super(InvoiceResource, self).gen_resp(resp, data)

    def invoice_xslt(self, content):
        try:
            xml_input = etree.fromstring(content)
            xslt_root = etree.parse(settings.INVOICE_XSLT_PATH)
            transform = etree.XSLT(xslt_root)
            return str(transform(xml_input))
        except Exception, e:
            logging.error("invoce_xslt_err with content: %s, "
                          "error: %s",
                          content,
                          str(e),
                          exc_info=True)
            raise ServerError("Invoice xslt error")

    def _on_post(self, req, resp, conn, **kwargs):
        id_order = req.get_param('order')

        if not id_order:
            raise ValidationError("Miss param in request")

        order = get_order(conn, id_order, self.users_id)
        if order is None:
            raise ValidationError("Order not exist")

        exist_invoice = get_invoice_by_order(conn, id_order)
        if len(exist_invoice) > 0:
            raise ValidationError("Invoice for Order: %s "
                                  "have already handled" % id_order)

        # address
        id_shipaddr = order['id_shipaddr']
        dest = get_user_dest_addr(conn, self.users_id, id_shipaddr)
        dest = ujson.dumps(dest)

        # customer
        user = get_user_profile(conn, self.users_id)
        customer = ' '.join([user['first_name'], user['last_name']])

        shipments = get_shipments_by_order(conn, id_order)

        invoices = {}
        for sp in shipments:
            invoice_xml = self.get_shipment_invoice(conn, dest, customer, sp)
            invoice = xmltodict.parse(invoice_xml)
            invoice_actor = ActorInvoices(data=invoice['invoices'])
            invoices[sp['id']] = (invoice_xml, invoice_actor)

        shipments_id = invoices.keys()
        shipments_id.sort()
        for id_shipment in shipments_id:
            self.save_invoice(conn,
                              id_order,
                              id_shipment,
                              invoices[id_shipment])

        content = self.gen_invoices_content(
            [invoices[id_shipment][0] for id_shipment in shipments_id])
        return {'content': content}

    def save_invoice(self, conn, id_order, id_shipment, invoice):
        invoice_xml = invoice[0]
        invoice_actor = invoice[1].invoices[0]
        return create_invoice(conn,
                              id_order,
                              id_shipment,
                              invoice_actor.total.value,
                              invoice_actor.currency,
                              invoice_xml,
                              invoice_actor.number)

    def gen_invoices_content(self, invoices_xml):
        invoices = []
        for xml in invoices_xml:
            content = xml[len(HEADER):].strip()
            content = content[len(DTD_HEADER):].strip()
            content = content[len(CONTENT_HEADER):]
            content = content[:-len(CONTENT_ROOT)]
            invoices.append(content)

        return invoices

    def get_shipment_invoice(self, conn, dest, customer, shipment):
        id_shipment = shipment['id']
        cal_method = shipment['calculation_method']
        id_shop = shipment['id_shop']
        id_brand = shipment['id_brand']
        query = {'customer': customer,
                 'dest': dest,
                 'shop': id_shop,
                 'brand': id_brand}

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

        return xml_invoice

    def shipment_content(self, conn, id_shipment):
        shipping_list = get_shipping_list(conn, id_shipment)

        content = []
        for shipping in shipping_list:
            content.append({"id_sale": shipping["id_sale"],
                            "id_variant": shipping["id_variant"],
                            "quantity": shipping["quantity"],
                            "id_price_type": shipping["id_price_type"]})

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
