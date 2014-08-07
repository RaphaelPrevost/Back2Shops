import settings
import ujson
import urllib
import urllib2
import xmltodict

from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import get_url_format
from views.base import BaseHtmlResource
from B2SUtils.base_actor import as_list
from B2SFrontUtils.constants import REMOTE_API_NAME

def get_payment_url(id_order, id_invoices):
    url = get_url_format(FRT_ROUTE_ROLE.PAYMENT)
    url += "?%s" % urllib.urlencode({
        'id_order': id_order,
        'id_invoices': ujson.dumps(id_invoices)
    })
    return url


class PaymentResource(BaseHtmlResource):
    template = "payment.html"
    show_products_menu = False
    login_required = {'get': True, 'post': True}

    def _on_get(self, req, resp, **kwargs):
        id_order = req.get_param('id_order')
        id_invoices = req.get_param('id_invoices')
        remote_resp = data_access(REMOTE_API_NAME.INIT_PAYMENT, req, resp,
                               order=id_order,
                               invoices=id_invoices)
        err = (remote_resp.get('error') or remote_resp.get('err')) \
              if isinstance(remote_resp, dict) else ""
        if err:
            id_trans = ""
            processors = []
        else:
            payment = xmltodict.parse(remote_resp)
            err = payment.get('error', {}).get('#text')
            if err:
                err = "Error Message: %s" % err
            processors = as_list(payment.get('payment', {}).get('processor'))
            id_trans = payment.get('payment', {}).get('@transaction')

        return {'step': 'init',
                'err': err,
                'id_trans': id_trans,
                'processors': processors}

    def _on_post(self, req, resp, **kwargs):
        id_trans = req.get_param('id_trans')
        processor = req.get_param('processor')
        id_order = req.get_param('id_order')
        invoices_obj = {}
        form = None
        if processor in ['1', '4']:
            trans = {'id_trans': id_trans}
            query = {'transaction': id_trans}
            invoices_obj = data_access(REMOTE_API_NAME.GET_INVOICES, req,
                                       resp, order=id_order,
                                       brand=settings.BRAND_ID)
            if processor == '1':
                query.update({
                    'processor': processor,
                    'success': settings.PP_SUCCESS % trans,
                    'failure': settings.PP_FAILURE % trans,
                })
            if processor == '4':
                query.update({
                    'processor': processor,
                    'success': settings.PB_SUCCESS % trans,
                    'failure': settings.PB_ERROR % trans,
                    'cancel': settings.PB_CANCEL % trans,
                    'waiting': settings.PB_WAITING % trans,
                })
            form_resp = data_access(REMOTE_API_NAME.PAYMENT_FORM, req, resp,
                                    **query)
            form = form_resp.get('form')
        if not form:
            form = '<div class="errwrapper">NOT_SUPPORTED</div>'
        return {'step': 'form',
                'form': form,
                'obj': invoices_obj,
                'order_id': id_order,
                'processor': processor}


class PaymentCancelResource(BaseHtmlResource):
    template = "payment_cancel.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        return {'result': kwargs}


class PaypalSuccessResource(BaseHtmlResource):
    template = "paypal_success.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        params = req._params
        params.update({'id_trans': kwargs['id_trans']})
        return {'result': params}


class PaypalFailureResource(BaseHtmlResource):
    template = "paypal_failure.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        params = req._params
        params.update({'id_trans': kwargs['id_trans']})
        return {'result': params}


class PayboxSuccessResource(BaseHtmlResource):
    template = "paybox_success.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        params = req._params
        params.update({'id_trans': kwargs['id_trans']})
        return {'result': params}


class PayboxFailureResource(BaseHtmlResource):
    template = "paybox_failure.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        params = req._params
        params.update({'id_trans': kwargs['id_trans']})
        return {'result': params}


class PayboxCancelResource(BaseHtmlResource):
    template = "paybox_failure.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        params = req._params
        params.update({'id_trans': kwargs['id_trans']})
        return {'result': params}


class PayboxWaitingResource(BaseHtmlResource):
    template = "paybox_failure.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        params = req._params
        params.update({'id_trans': kwargs['id_trans']})
        return {'result': params}
