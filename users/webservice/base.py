from common import db_utils
from common.error import ValidationError
from common.utils import cookie_verify
from common.utils import gen_json_response
from common.constants import RESP_RESULT

class BaseResource:
    login_required = {'get': False, 'post': False}

    def on_get(self, req, resp, **kwargs):
        self._msg_handler('get', req, resp, **kwargs)

    def on_post(self, req, resp, **kwargs):
        self._msg_handler('post', req, resp, **kwargs)

    def _msg_handler(self, method_name, req, resp, **kwargs):
        with db_utils.get_conn() as conn:
            try:
                if self.login_required.get(method_name):
                    cookie_verify(conn, req, resp)
                method = getattr(self, '_on_' + method_name)
                method(req, resp, conn, **kwargs)
            except ValidationError, e:
                return gen_json_response(resp,
                         {'res': RESP_RESULT.F,
                          'err': str(e)})

    def _on_get(self, req, resp, conn, **kwargs):
        pass

    def _on_post(self, req, resp, conn, **kwargs):
        pass

