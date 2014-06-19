import urllib
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import get_url_format
from views.base import BaseHtmlResource
from B2SProtocol.constants import RESP_RESULT
from B2SFrontUtils.constants import REMOTE_API_NAME


class UserResource(BaseHtmlResource):
    template = "user_info.html"

    def _on_get(self, req, resp, **kwargs):
        remote_resp = data_access(REMOTE_API_NAME.GET_USERINFO,
                                  req, resp)
        err = req.get_param('err') or ''
        user_profile = {}
        if remote_resp.get('res') == RESP_RESULT.F:
            err = remote_resp.get('err')
        else:
            user_profile = remote_resp
        return {'user_profile': user_profile, 'err': err}

    def _on_post(self, req, resp, **kwargs):
        remote_resp = data_access(REMOTE_API_NAME.SET_USERINFO,
                                  req, resp,
                                  action="modify",
                                  **req._params)
        if remote_resp.get('res') == RESP_RESULT.F:
            err = remote_resp.get('err')
        else:
            err = ''
        self._redirect(err)

    def _redirect(self, err):
        url = get_url_format(FRT_ROUTE_ROLE.ORDER_USER)
        if err:
            url += "?err=%s" % urllib.quote(err)
        self.redirect(url)
