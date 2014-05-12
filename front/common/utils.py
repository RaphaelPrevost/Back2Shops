import settings
from common.constants import FRT_ROUTE_ROLE
from common.template import render_template

def gen_html_resp(template, resp, data, lang='en'):
    resp.body = render_template(template, data, lang=lang)
    resp.content_type = "text/html"
    return resp

def unicode2utf8(data):
    """Convert unicode string's into utf-8 encoding
    This utility function will accept dict and list data structures.
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            key = unicode2utf8(key)
            value = unicode2utf8(value)
            result[key] = value
    elif isinstance(data, list):
        result = []
        for value in data:
            value = unicode2utf8(value)
            result.append(value)
    elif isinstance(data, unicode):
        result = data.encode('utf-8')
    else:
        result = data
    return result

def get_brief_product_list(sales):
    product_list = []
    for _id, info in sales.iteritems():
        product_info = {
            'id': _id,
            'name': info.get('name') or '',
            'desc': info.get('desc') or '',
            'img': info.get('img') or '',
            'link': get_url_format(FRT_ROUTE_ROLE.PRDT_INFO) % _id,
        }
        if not settings.PRODUCTION and not product_info['img']:
            product_info['img'] = '/img/dollar-exemple.jpg'
        product_list.append(product_info)

    return product_list

def get_url_format(role):
    #TODO get url format from BO
    return {
        FRT_ROUTE_ROLE.PRDT_LIST: '/products',
        FRT_ROUTE_ROLE.PRDT_INFO: '/products/%s',
    }.get(role)
