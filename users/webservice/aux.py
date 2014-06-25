import settings
from common.cache import find_cache_proxy
from common import field_utils
from webservice.base import BaseJsonResource
from B2SProtocol.constants import RESP_RESULT
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from B2SRespUtils.generate import gen_json_resp


class AuxResource(BaseJsonResource):
    get_res_func_map = {
        'titles': 'handle_titles',
        'countries': 'handle_countries',
        'provinces': 'handle_provinces',
        'sales': 'handle_sales',
    }

    def _on_get(self, req, resp, conn, **kwargs):
        res_name = req.get_param('get')
        if res_name not in self.get_res_func_map:
            raise ValidationError('INVALID_REQUEST')
        func = getattr(self, self.get_res_func_map[res_name], None)
        assert hasattr(func, '__call__')
        return func(req, resp, conn)

    def on_post(self, req, resp, **kwargs):
        return gen_json_resp(resp,
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
        return field.toDict()

    def handle_countries(self, req, resp, conn):
        dep_val = req.get_param('dep') or ''
        cur_val = req.get_param('val') or ''

        result = db_utils.select(conn, "country",
                                columns=("printable_name", "iso"))
        field = field_utils.SelectFieldType("Country",
                                            cur_val, dict(result))
        return field.toDict()

    def handle_provinces(self, req, resp, conn):
        dep_val = req.get_param('dep') or ''
        cur_val = req.get_param('val') or ''

        if dep_val in settings.SUPPORTED_MAJOR_COUNTRIES:
            result = db_utils.select(conn, "province",
                                    columns=("name", "code"),
                                    where={'country_code': dep_val})
        else:
            result = []

        field = field_utils.SelectFieldType("Province",
                                            cur_val, dict(result))
        return field.toDict()

    def handle_sales(self, req, resp, conn):
        sales_list = find_cache_proxy.get(req.query_string)
        return sales_list
