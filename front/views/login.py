from common.data_access import data_access
from views.base import BaseHtmlResource
from B2SUtils.errors import ValidationError
from B2SFrontUtils.constants import REMOTE_API_NAME


class LoginResource(BaseHtmlResource):
    template = "login.html"

    def _on_post(self, req, resp, **kwargs):
        email = req.get_param('email')
        password = req.get_param('password')
        if not email:
            raise ValidationError('ERR_EMAIL')
        if not password:
            raise ValidationError('ERR_PASSWORD')

        remote_resp = data_access(REMOTE_API_NAME.LOGIN,
                                  req, resp,
                                  email=email,
                                  password=password)
        return remote_resp
