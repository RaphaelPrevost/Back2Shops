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
import ujson

from B2SFrontUtils.constants import REMOTE_API_NAME
from common.data_access import data_access
from common.utils import get_brief_product_list
from views.base import BaseHtmlResource

class HomepageResource(BaseHtmlResource):
    template = 'index.html'

    def _on_get(self, req, resp, **kwargs):
        sales = data_access(REMOTE_API_NAME.GET_SALES,
                            req, resp, **req._params)

        data = {'product_list': get_brief_product_list(sales, req, resp)}

        if settings.BRAND_NAME == 'DRAGONDOLLAR':
            dd_data = self.dragondollar_data(req, resp)
            data.update(dd_data)

        return data

    def dragondollar_data(self, req, resp):
        data = {}
        slides = data_access(REMOTE_API_NAME.GET_SLIDE_SHOW,
                             req, resp, **req._params)
        data['slides'] = slides.get('slideshow', {}).get('slide', [])

        try:
            with open(settings.DRAGON_FEED_CACHE_PATH, 'r') as f:
                data['coins'] = ujson.load(f)
        except IOError:
            pass

        return data


class EShopResource(BaseHtmlResource):
    template = 'eshop.html'
    cur_tab_index = 0

class LookbookResource(BaseHtmlResource):
    template = 'lookbook.html'
    cur_tab_index = 1

class LaSagaResource(BaseHtmlResource):
    template = 'lasaga.html'
    cur_tab_index = 2

class MentionLegalResource(BaseHtmlResource):
    template = 'mention_legal.html'

class CGVResource(BaseHtmlResource):
    template = 'cgv.html'

class CommandsAndDeliveriesResource(BaseHtmlResource):
    template = 'commands_deliveries.html'
