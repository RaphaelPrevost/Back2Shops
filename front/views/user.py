from common.data_access import data_access
from views.base import BaseHtmlResource
from B2SProtocol.constants import RESP_RESULT
from B2SFrontUtils.constants import REMOTE_API_NAME


class UserResource(BaseHtmlResource):
    template = "user_info.html"

    def _on_get(self, req, resp, **kwargs):
        remote_resp = data_access(REMOTE_API_NAME.GET_USERINFO,
                                  req, resp)
        user_profile = {}
        if remote_resp.get('res') == RESP_RESULT.F:
            err = remote_resp.get('err')
        else:
            user_profile = remote_resp
            err = ''
        return {'user_profile': user_profile, 'err': err}

