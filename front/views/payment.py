import settings
import urllib
import urllib2

from views.base import BaseHtmlResource


class PaymentSuccessResource(BaseHtmlResource):
    template = "payment_success.html"

    def _on_get(self, req, resp, **kwargs):
        params = req._params
        params.update({'id_trans': kwargs['id_trans']})
        return {'result': params}


class PaymentFailureResource(BaseHtmlResource):
    template = "payment_failure.html"

    def _on_get(self, req, resp, **kwargs):
        params = req._params
        params.update({'id_trans': kwargs['id_trans']})
        return {'result': params}

# TODO: REMOVE, this is just for test
class PaymentFormResource(BaseHtmlResource):
    def _on_get(self, req, resp, **kwargs):
        id_trans = kwargs['id_trans']
        trans = {'id_trans': id_trans}
        query = {'transaction': id_trans,
                 'processor': 1,
                 'success': settings.PM_SUCCESS % trans,
                 'failure': settings.PM_FAILURE % trans}
        query_string = urllib.urlencode(query)
        url = '?'.join([settings.USER_PM_FORM_URL, query_string])
        req = urllib2.Request(url)
        resp = urllib2.urlopen(req)
        form = resp.read()
        return form


