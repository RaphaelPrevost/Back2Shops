# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


import settings

from B2SProtocol.constants import RESP_RESULT
from B2SRespUtils.generate import gen_json_resp
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from common import field_utils
from common.cache import find_cache_proxy
from webservice.base import BaseJsonResource


class AuxResource(BaseJsonResource):
    get_res_func_map = {
        'titles': 'handle_titles',
        'countries': 'handle_countries',
        'provinces': 'handle_provinces',
        'sales': 'handle_sales',
        'province_code': 'get_province_code_by_name',
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
                                            cur_val, result)
        return field.toDict()

    def handle_countries(self, req, resp, conn):
        dep_val = req.get_param('dep') or ''
        cur_val = req.get_param('val') or ''

        result = db_utils.select(conn, "country",
                                columns=("printable_name", "iso"),
                                order=("printable_name",))
        field = field_utils.SelectFieldType("Country",
                                            cur_val, result)
        return field.toDict()

    def handle_provinces(self, req, resp, conn):
        dep_val = req.get_param('dep') or ''
        cur_val = req.get_param('val') or ''

        if dep_val in settings.SUPPORTED_MAJOR_COUNTRIES:
            result = db_utils.select(conn, "province",
                                    columns=("name", "code"),
                                    where={'country_code': dep_val},
                                    order=("name",))
        else:
            result = []

        field = field_utils.SelectFieldType("Province",
                                            cur_val, result)
        return field.toDict()

    def handle_sales(self, req, resp, conn):
        sales_list = find_cache_proxy.get(req.query_string)
        return sales_list

    def get_province_code_by_name(self, req, resp, conn):
        country_code = req.get_param('ccode') or ''
        province_name = req.get_param('pname') or ''
        if country_code and province_name:
            query = ('SELECT code FROM province WHERE country_code = %s AND '
                     '(name = %s OR geoip_name = %s) LIMIT 1')
            result = db_utils.query(
                conn, query, (country_code, province_name, province_name))
            if result:
                result = result[0] and result[0][0] or ''
        else:
            result = ''
        return result
