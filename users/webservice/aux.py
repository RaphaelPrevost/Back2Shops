import settings
from common.constants import RESP_RESULT
from common.error import ValidationError
from common import db_utils
from common import field_utils
from common.utils import gen_json_response
from webservice.base import BaseResource

class AuxResource(BaseResource):
    get_res_func_map = {
        'titles': 'handle_titles',
        'countries': 'handle_countries',
        'provinces': 'handle_provinces',
    }

    def _on_get(self, req, resp, conn, **kwargs):
        res_name = req.get_param('get')
        if res_name not in self.get_res_func_map:
            raise ValidationError('INVALID_REQUEST')
        func = getattr(self, self.get_res_func_map[res_name], None)
        assert hasattr(func, '__call__')
        return func(req, resp, conn)

    def on_post(self, req, resp, **kwargs):
        return gen_json_response(resp,
                    {'res': RESP_RESULT.F,
                     'err': 'INVALID_REQUEST'})

    def handle_titles(self, req, resp, conn):
        dep_val = req.get_param('dep') or ''
        cur_val = req.get_param('val') or ''

        result = db_utils.select(conn, "title",
                                columns=("title", "title"),
                                where={'locale': dep_val})
        field = field_utils.SelectFieldType("Title",
                                            cur_val, dict(result))
        return gen_json_response(resp, field.toDict())

    def handle_countries(self, req, resp, conn):
        dep_val = req.get_param('dep') or ''
        cur_val = req.get_param('val') or ''

        result = db_utils.select(conn, "country",
                                columns=("printable_name", "iso"))
        field = field_utils.SelectFieldType("Country",
                                            cur_val, dict(result))
        return gen_json_response(resp, field.toDict())

    def handle_provinces(self, req, resp, conn):
        dep_val = req.get_param('dep') or ''
        cur_val = req.get_param('val') or ''

        if dep_val not in settings.SUPPORTED_MAJOR_COUNTRIES:
            raise ValidationError('INVALID_REQUEST')

        result = db_utils.select(conn, "province",
                                columns=("name", "code"),
                                where={'country_code': dep_val})
        field = field_utils.SelectFieldType("Province",
                                            cur_val, dict(result))
        return gen_json_response(resp, field.toDict())

