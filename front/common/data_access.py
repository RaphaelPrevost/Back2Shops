# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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
from common.redis_utils import get_redis_cli
from common.utils import unicode2utf8
from B2SCrypto.constant import SERVICES
from B2SFrontUtils.api import remote_call
from B2SFrontUtils.cache import cache_proxy
from B2SFrontUtils.constants import USR_API_SETTINGS


def data_access(api_name, req=None, resp=None, **kwargs):
    if 'seller' not in kwargs \
            and 'brand' not in kwargs \
            and 'brand_id' not in kwargs:
        kwargs['brand'] = settings.BRAND_ID

    resp_dict = {}
    pri_key_path = settings.PRIVATE_KEY_PATH
    usr_pub_key_uri = settings.SERVER_APIKEY_URI_MAP[SERVICES.USR]
    if api_name in cache_proxy:
        resp_dict = cache_proxy[api_name](get_redis_cli(),
                                          settings.USR_ROOT_URI,
                                          pri_key_path,
                                          usr_pub_key_uri).get(**kwargs)
    elif api_name in USR_API_SETTINGS:
        resp_dict = remote_call(settings.USR_ROOT_URI,
                                api_name,
                                pri_key_path,
                                usr_pub_key_uri,
                                req, resp,
                                **kwargs)
    else:
        pass
    return unicode2utf8(resp_dict)

