from common.data_access import data_access
from views.base import BaseHtmlResource
from views.base import BaseJsonResource
from B2SProtocol.constants import RESP_RESULT
from B2SUtils.errors import ValidationError
from B2SFrontUtils.constants import REMOTE_API_NAME

def register(req, resp, **kwargs):
    email = req.get_param('email')
    password = req.get_param('password')
    password2 = req.get_param('password2')
    if not email:
        raise ValidationError('ERR_EMAIL')
    if not password or password != password2:
        raise ValidationError('ERR_PASSWORD')

    remote_resp = data_access(REMOTE_API_NAME.REGISTER,
                              req, resp,
                              action="create",
                              email=email,
                              password=password)
    return remote_resp

class RegisterAPIResource(BaseJsonResource):
    def _on_post(self, req, resp, **kwargs):
        remote_resp = register(req, resp, **kwargs)
        if remote_resp.get('res') == RESP_RESULT.S:
            email = req.get_param('email')
            password = req.get_param('password')
            data_access(REMOTE_API_NAME.LOGIN,
                        req, resp,
                        email=email,
                        password=password)
        return remote_resp
