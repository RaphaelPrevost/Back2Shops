import settings
import logging
import ujson
import urllib
import xmltodict

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SUtils.base_actor import as_list
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import get_order_table_info
from common.utils import get_url_format
from common.utils import get_valid_attr
from views.base import BaseHtmlResource

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
            if settings.BRAND_NAME == "BREUER":
                #hardcode paybox for BREUER
                return self._payment_form(req, resp,
                                          id_trans=id_trans,
                                          processor='4',
                                          id_order=id_order)

        data = {'step': 'init',
                'err': err,
                'id_trans': id_trans,
                'processors': processors,
                'id_order': id_order}
        return data

    def _on_post(self, req, resp, **kwargs):
        return self._payment_form(req, resp, **kwargs)

    def _payment_form(self, req, resp, **kwargs):
        id_trans = req.get_param('id_trans') or kwargs.get('id_trans')
        processor = req.get_param('processor') or kwargs.get('processor')
        id_order = req.get_param('id_order') or kwargs.get('id_order')
        form = None
        if processor in ['1', '4']:
            trans = {'id_trans': id_trans}
            query = {'transaction': id_trans}
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

        data = {'step': 'form',
                'form': form,
                'order_id': id_order,
                'processor': processor}
        user_info = data_access(REMOTE_API_NAME.GET_USERINFO,
                                req, resp)
        order_resp = data_access(REMOTE_API_NAME.GET_ORDER_DETAIL, req, resp,
                                 id=id_order, brand_id=settings.BRAND_ID)

        order_data = get_order_table_info(id_order, order_resp)
        data.update(order_data)
        return data


class PaymentCancelResource(BaseHtmlResource):
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        return self.redirect(get_url_format(FRT_ROUTE_ROLE.ORDER_LIST))


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


class PaypalCancelResource(PaymentCancelResource):
    pass


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


class PayboxCancelResource(PaymentCancelResource):
    pass


class PayboxWaitingResource(BaseHtmlResource):
    template = "paybox_failure.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        params = req._params
        params.update({'id_trans': kwargs['id_trans']})
        return {'result': params}
