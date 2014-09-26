import settings
import gevent
import ujson

from B2SUtils.base_actor import as_list
from B2SUtils.email_utils import send_email
from B2SRespUtils.generate import _temp_content as render_content
from common.utils import cur_symbol
from common.utils import to_unicode
from models.order import get_order_detail
from models.user import get_user_email

def send_html_email(to, subject, content):
    if not settings.SEND_EMAILS:
        return
    send_email(settings.SERVICE_EMAIL, to, subject, content, settings)

def send_order_email(conn, id_order):
    order_resp = get_order_detail(conn, id_order, 0)
    user_profile = order_resp.get('user_info')
    first_name = user_profile.get('first_name')
    user_email = get_user_email(conn, user_profile.get('users_id'))

    shipping_lists = []
    for item in order_resp.get('order_items', []):
        for item_id, item_info in item.iteritems():
            id_sale = str(item_info['sale_id'])

            if item_info['id_variant'] == 0:
                product_name = item_info['name']
                variant_name = ''
            else:
                product_name, variant_name = item_info['name'].rsplit('-', 1)
            one = {
                'id_sale': id_sale,
                'quantity': item_info['quantity'],
                'product_name': product_name,
                'variant_name': variant_name,
                'type_name': item_info.get('type_name') or '',
                'price': item_info['price'],
                'picture': item_info['picture'],
            }

            item_invoice_info = {}
            for iv in item_info['invoice_info']:
                iv_item_info = ujson.loads(iv['invoice_item'])
                if iv_item_info:
                    taxes = as_list(iv_item_info.get('tax', {}))
                    iv['tax'] = sum([float(t['#text']) for t in taxes
                                     if t.get('@to_worldwide') == 'True'
                                        or t.get('@show') == 'True'])
                    iv['tax_per_item'] = iv['tax'] / int(iv_item_info['qty'])
                    iv['show_final_price'] = len(
                        [t for t in taxes if t.get('@show') == 'True']) > 0
                else:
                    iv['tax'] = 0
                    iv['tax_per_item'] = 0
                    iv['show_final_price'] = False
                item_invoice_info[iv['shipment_id']] = iv

            for _shipment_info in item_info['shipment_info']:
                shipment_id = _shipment_info.get('shipment_id')
                if not shipment_id:
                    # sth. wrong when create order
                    continue
                shipping_list = _shipment_info.copy()
                shipping_list.update(item_invoice_info.get(shipment_id))
                shipping_list['item'] = one
                shipping_list['currency'] = cur_symbol(shipping_list['currency'])
                shipping_lists.append(shipping_list)

    data = {
        'first_name': first_name,
        'order_id': id_order,
        'shipping_lists': shipping_lists,
        'order_invoice_url': settings.FRONT_ORDER_INVOICE_URL
                             % {'id_order': id_order},
    }
    email_content = render_content('order_email.html',
                                   base_url=settings.FRONT_ROOT_URI,
                                   **to_unicode(data))
    gevent.spawn(send_html_email,
                 user_email,
                 settings.ORDER_EMAIL_SUBJECT,
                 email_content)
    return data
