import settings
from common.redis_utils import get_redis_cli
from common.utils import unicode2utf8
from B2SFrontUtils.api import remote_call
from B2SFrontUtils.cache import cache_proxy
from B2SFrontUtils.constants import USR_API_SETTINGS


def data_access(api_name, req=None, resp=None, **kwargs):
    kwargs['brand'] = settings.BRAND_ID

    resp_dict = {}
    if api_name in cache_proxy:
        resp_dict = cache_proxy[api_name](get_redis_cli(),
                                          settings.USR_ROOT_URI).get(**kwargs)
    elif api_name in USR_API_SETTINGS:
        resp_dict = remote_call(settings.USR_ROOT_URI,
                                api_name, req, resp, **kwargs)
    else:
        pass
    return unicode2utf8(resp_dict)

