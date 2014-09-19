import settings
import unittest
import ujson
import xmltodict

from common.test_utils import is_backoffice_server_running
from common.test_utils import is_finace_server_running
from models.actors.error import ActorError
from models.actors.payment import ActorPayment
from tests.base_order_test import BaseShipmentTestCase
from B2SUtils import db_utils
from B2SProtocol.constants import TRANS_STATUS

SKIP_REASON = "Please run backoffice server before running this test"
FIN_SKIP_REASON = "Please run finance server before running this test"
FIN_RUNNING_SKIP_REASON = "Please stop finance server before running this test"

FRONT_PAYMENT_SUCCESS = "%s/paypal/%%(id_trans)s/success" % settings.FRONT_ROOT_URI
FRONT_PAYMENT_FAILURE = "%s/paypal/%%(id_trans)s/failure" % settings.FRONT_ROOT_URI

class TestPayment(BaseShipmentTestCase):
    @unittest.skipUnless(is_finace_server_running(), FIN_SKIP_REASON)
    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def test(self):
        id_order, expect_due = self._set_order()
        id_trans = self._send_payment_init(id_order, expect_due)
        self._send_payment_form(id_trans)

    @unittest.skipIf(is_finace_server_running(), FIN_RUNNING_SKIP_REASON)
    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def test_fin_server_down(self):
        id_order, expect_due = self._set_order()
        self._send_payment_init(id_order, expect_due, fin_down=True)

    def _set_order(self):
        # Address info:
            #  * shop 5 address: US - AL
            #  * shop 6 address: US - AL
            #  * user address: US - AL

            # Sale items info:
            #  * item1: shop5
            #           not allow group
            #           support EMS-Express
            #           handling fee: 1
            #           weight: 1
            #           quantity: 2
            #  * item2: shop6
            #           allow group
            #           support EMS-Express
            #           handling fee: 2
            #           weight: 2
            #           quantity: 3

        # update user address to US AL
        self.b.update_account_address(self.users_id,
                                      "US",
                                      "AL",
                                      "ALABAMA")

        item1_quantity = 2
        item2_quantity = 3
        item1_in_shop5 = {
            'id_sale': 1000027,
            'id_variant': 0,
            'quantity': item1_quantity,
            'id_shop': 1000005,
            'id_price_type': 0,
            'id_weight_type': 0}
        item2_in_shop6 ={
            'id_sale': 1000028,
            'id_variant': 0,
            'quantity': item2_quantity,
            'id_shop': 1000006,
            'id_price_type': 0,
            'id_weight_type': 0}


        # sale items info configured in backoffice
        item1_price = 1
        item1_weight = 1
        item1_handling_fee = 1
        item1_shipping_fee = 2.0 * item1_weight
        item2_price = 2
        item2_weight = 2
        item2_handling_fee = 2
        item2_shipping_fee = 2.0 * item2_weight

        # taxes info configured in backoffice
        # US to US: 1%
        # US AL to US AL: 0.5%
        # US AL to US AL shipping fee: 1%
        tax1 = 0.01
        tax2 = 0.005
        tax3 = 0.01 # taxable

        wwwOrder = [item1_in_shop5, item2_in_shop6]

        id_order = self.success_wwwOrder(self.telephone,
                                         self.shipaddr,
                                         self.billaddr,
                                         wwwOrder)
        self._shipmentsCountCheck(id_order, 3)

        iv1_due = (item1_price +
                   item1_price * (tax1 + tax2 + tax3) +
                   (item1_handling_fee + item1_shipping_fee * 1) +
                   (item1_handling_fee + item1_shipping_fee * 1) * tax3)
        iv2_due = (item1_price +
                   item1_price * (tax1 + tax2 + tax3) +
                   (item1_handling_fee + item1_shipping_fee * 1) +
                   (item1_handling_fee + item1_shipping_fee * 1) * tax3)
        iv3_due = (item2_price * item2_quantity +
                   item2_price * item2_quantity * (tax1 + tax2 + tax3) +
                   (item2_handling_fee + item2_shipping_fee * item2_quantity) +
                   (item2_handling_fee + item2_shipping_fee * item2_quantity) * tax3)

        expect_due = (iv1_due + iv2_due + iv3_due)
        self.b.post_invoices(id_order)
        self.expect_invoices_due(id_order, expect_due)

        return id_order, expect_due

    def _expect_trans(self, id_trans, exp_order=None, exp_invoices=None,
                      exp_status=None, exp_amount_due=None,
                      exp_processor=None, exp_success=None, exp_failure=None
    ):

        sql = """SELECT * from transactions where id = %s"""
        with db_utils.get_conn() as conn:
            trans = db_utils.query(conn, sql, (id_trans,))
        self.assertEqual(len(trans),
                         1,
                         "no expected trans for %s" % id_trans)

        trans = trans[0]
        expect = {'id_order': exp_order,
                  'id_invoices': exp_invoices,
                  'status': exp_status,
                  'amount_due': exp_amount_due,
                  'id_processor': exp_processor,
                  'url_success': exp_success,
                  'url_failure': exp_failure,
                  'id_user': int(self.users_id),
                  }
        cookie_fields = ['amount_due', 'id_order', 'id_user', 'id_invoices']
        for k, v in expect.iteritems():
            if v is not None and k != 'id_user':
                self.assertEqual(
                    trans[k],
                    v,
                    '%s is not as expected: %s - %s'
                    % (k, trans[k], v))
            if k in cookie_fields and v is not None:
                cookie = ujson.loads(trans['cookie'])
                self.assertEqual(
                    cookie[k],
                    v,
                    '%s in cookie is not as expected: %s - %s'
                    % (k, cookie[k], v))


    def _send_payment_init(self, id_order, expect_due, fin_down=False):
        id_invoices = self._get_order_invoices(id_order)
        id_invoices = ujson.dumps(id_invoices)

        resp = self.b._access("webservice/1.0/pub/payment/init",
                              {'order': id_order,
                               'invoices': id_invoices})
        data = xmltodict.parse(resp.read())
        if fin_down:
            actor_error = ActorError(data=data['error'])
            self.assertEqual(
                actor_error.err,
                'SERVER ERROR',
                "pm init err is not as expected: %s - %s"
                % (actor_error.err, 'SERVER ERROR'))
        else:
            actor_pm_init = ActorPayment(data=data['payment'])
            id_trans = actor_pm_init.transaction
            self._expect_trans(id_trans,
                               exp_order=int(id_order),
                               exp_invoices=id_invoices,
                               exp_status=TRANS_STATUS.TRANS_OPEN,
                               exp_amount_due=expect_due,
                               )
            return id_trans

    def _send_payment_form(self, id_trans):
        trans = {'id_trans': id_trans}
        success_url = FRONT_PAYMENT_SUCCESS % trans
        failure_url = FRONT_PAYMENT_FAILURE % trans

        resp = self.b._access("webservice/1.0/pub/payment/form",
                       {'transaction': id_trans,
                       'processor': 1,
                       'success': success_url,
                       'failure': failure_url})
        resp = resp.read()

        self._expect_trans(id_trans,
                           exp_processor=1,
                           exp_success=success_url,
                           exp_failure=failure_url
                           )

        self.assert_(
            settings.PAYMENT_PAYPAL_RETURN % trans in resp)
        self.assert_(
            settings.PAYMENT_PAYPAL_CANCEL % trans in resp)
        self.assert_(
            settings.PAYMENT_PAYPAL_GATEWAY % trans in resp)

    def expect_invoices_due(self, id_order, exp_amount_due):
        sql = """SELECT sum(amount_due)
                   FROM invoices
                  WHERE id_order = %s
        """
        with db_utils.get_conn() as conn:
            amount_due = db_utils.query(conn, sql, (id_order,))
            amount_due = amount_due[0][0]
            self.assertEqual(amount_due,
                             exp_amount_due,
                             "amount_due %s is not same with expected: %s"
                             % (amount_due, exp_amount_due))

    def _get_order_invoices(self, id_order):
        sql = """SELECT id FROM invoices where id_order = %s"""

        with db_utils.get_conn() as conn:
            r = db_utils.query(conn, sql, (id_order,))
            return [i['id'] for i in r]
