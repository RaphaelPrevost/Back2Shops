import settings
import ujson

from models.transaction import create_trans
from models.transaction import update_trans
from models.processor import get_processor
from webservice.base import BaseJsonResource

from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.constant import SERVICES
from B2SRespUtils.generate import temp_content

class PaymentResource(BaseJsonResource):
    encrypt = True

    def _on_post(self, req, resp, conn, **kwargs):
        data = decrypt_json_resp(req.stream,
                                 settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                                 settings.PRIVATE_KEY_PATH)
        data = ujson.loads(data)

        id_trans = create_trans(conn,
                                data['order'], data['user'],
                                data['invoices'], data['amount'],
                                data['invoicesData'])

        pm_cookie = {"id_user": data['user'],
                     "id_order": data['order'],
                     "amount_due": data['amount'],
                     "id_invoices": data['invoices'],
                     "internal_trans": id_trans}

        pm_cookie = ujson.dumps(pm_cookie)
        update_trans(conn,
                     {'cookie': pm_cookie},
                     where={'id': id_trans})

        pm_init = self.procession_options(conn)
        return {'pm_init': pm_init,
                'cookie': pm_cookie}

    def procession_options(self, conn):
        proc_list = get_processor(conn)
        data = {'obj_list': proc_list}
        return temp_content("processor.xml", **data)
