import urllib
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import get_url_format
from views.base import BaseHtmlResource
from views.base import BaseJsonResource
from B2SProtocol.constants import RESP_RESULT
from B2SFrontUtils.constants import REMOTE_API_NAME


class UserAuthResource(BaseHtmlResource):
    template = "user_auth.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        return {'succ_redirect_to': get_url_format(FRT_ROUTE_ROLE.USER_INFO)}


class UserResource(BaseHtmlResource):
    template = "user_info.html"
    show_products_menu = False
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, **kwargs):
        return self._get_user_info(req, resp)

    def _get_user_info(self, req, resp):
        remote_resp = data_access(REMOTE_API_NAME.GET_USERINFO,
                                  req, resp)
        err = req.get_param('err') or ''
        user_profile = {}
        if remote_resp.get('res') == RESP_RESULT.F:
            err = remote_resp.get('err')
        else:
            user_profile = remote_resp
        return {'user_profile': user_profile,
                'err': err,
                'succ_redirect_to': ''}


class UserAPIResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}

    def _on_post(self, req, resp, **kwargs):
        remote_resp = data_access(REMOTE_API_NAME.SET_USERINFO,
                                  req, resp,
                                  action="modify",
                                  **req._params)
        resp_dict = {}
        resp_dict.update(remote_resp)
        return resp_dict
