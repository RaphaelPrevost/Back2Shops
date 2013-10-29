import copy
import logging
import time
from datetime import datetime

from common.utils import gen_html_resp
from common.utils import gen_pdf_resp
from common.utils import gen_400_html_resp
from common.utils import gen_400_pdf_resp
from common.utils import gen_500_html_resp
from common.utils import gen_500_pdf_resp
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError

class BaseResource:
    template = ''
    def on_get(self, req, resp, **kwargs):
        self._msg_handler('get', req, resp, **kwargs)

    def on_post(self, req, resp, **kwargs):
        self._msg_handler('post', req, resp, **kwargs)

    def _msg_handler(self, method_name, req, resp, **kwargs):
        start_time = time.time() * 1000
        params = req._params
        if params.get('password'):
            params = copy.copy(req._params)
            params['password'] = '******'
        try:
            with db_utils.get_conn() as conn:
                logging.info('Got %s requet at %s UTC, %s with params %s'
                              % (req.method, datetime.utcnow(),
                                 req.uri, params))
                method = getattr(self, '_on_' + method_name)
                method(req, resp, conn, **kwargs)
        except ValidationError, e:
            logging.error('Bad Request Err: %s, query: %s',
                          e, req.query_string, exc_info=True)
            self._handle_bad_request_err(resp)
        except Exception, e:
            logging.error('Server Error: %s, query: %s',
                          e, req.query_string, exc_info=True)
            self._handle_bad_request_err(resp)
        end_time = time.time() * 1000
        logging.info('Response %s Request: %s params: %s, With: %s in %s ms'
                     % (req.method, req.uri, params,
                        resp.body, end_time - start_time))

    def _handle_server_err(self, resp):
        """ 500 internal server error.
        """
        pass

    def _handle_bad_request_err(self, resp):
        """ 400 bad request error.
        """
        pass

    def _do_get(self, req, resp, conn, **kwargs):
        pass

    def _do_post(self, req, resp, conn, **kwargs):
        pass

    def _on_get(self, req, resp, conn, **kwargs):
        return self._do_get(req, resp, conn, **kwargs)

    def _on_post(self, req, resp, conn, **kwargs):
        return self._do_post(req, resp, conn, **kwargs)


class BaseHtmlResource(BaseResource):
    def _on_get(self, req, resp, conn, **kwargs):
        result = self._do_get(req, resp, conn, **kwargs)
        return gen_html_resp(self.template, resp, **result)

    def _on_post(self, req, resp, conn, **kwargs):
        result = self._do_post(req, resp, conn, **kwargs)
        return gen_html_resp(self.template, resp, **result)

    def _do_get(self, req, resp, conn, **kwargs):
        return {}

    def _do_post(self, req, resp, conn, **kwargs):
        return {}

    def _handle_server_err(self, resp):
        """ 500 internal server error.
        """
        return gen_500_html_resp(resp)

    def _handle_bad_request_err(self, resp):
        """ 400 bad request error.
        """
        return gen_400_html_resp(resp)


class BasePdfResource(BaseResource):
    def _on_get(self, req, resp, conn, **kwargs):
        result = self._do_get(req, resp, conn, **kwargs)
        return gen_pdf_resp(self.template, resp, **result)

    def _on_post(self, req, resp, conn, **kwargs):
        result = self._do_post(req, resp, conn, **kwargs)
        return gen_pdf_resp(self.template, resp, **result)

    def _do_get(self, req, resp, conn, **kwargs):
        return {}

    def _do_post(self, req, resp, conn, **kwargs):
        return {}

    def _handle_server_err(self, resp):
        """ 500 internal server error.
        """
        return gen_400_pdf_resp(resp)

    def _handle_bad_request_err(self, resp):
        """ 400 bad request error.
        """
        return gen_500_pdf_resp(resp)
