import logging
import ujson
import settings

from datetime import datetime, timedelta

from common.constants import USERS_ROLE
from common.constants import TARGET_MARKET_TYPES
from django.db.models import Q
from django.http import HttpResponse
from fouillis.views import OperatorUpperLoginRequiredMixin
from django.views.generic import View
from redis.exceptions import ConnectionError
from stats.models import Incomes, Orders, Visitors

from B2SCrypto.utils import get_from_remote
from B2SCrypto.constant import SERVICES
from B2SProtocol.constants import ORDER_STATUS
from B2SUtils.redis_cli import redis_cli

DT_FORMAT = "%m-%d"

class StatsView(OperatorUpperLoginRequiredMixin, View):
    def gen_week_days(self):
        today = datetime.utcnow().date()
        return [today - timedelta(days=i) for i in range(0, 7)]


class StatsIncomesView(StatsView):
    def get(self, request, *args, **kwargs):
        user = request.user
        week_days = self.gen_week_days()
        incomes = []

        for date in week_days:
            income = self._day_income(user, date)
            incomes.append([date.strftime(DT_FORMAT), income])

        obj = {'earned_today': incomes[0][1],
               'lines': incomes}

        print incomes

        return HttpResponse(ujson.dumps(obj), mimetype="application/json")

    def _day_income(self, user, date):
        # from_/to limit
        from_ = date
        to = date + timedelta(days=1)
        q = Q(up_time__gte=from_) & Q(up_time__lt=to)
        if not user.is_superuser:
            req_u_profile = user.get_profile()
            brand_id = req_u_profile.work_for
            if req_u_profile.role == USERS_ROLE.ADMIN:
                # brand limit for brand admin
                q = q & Q(sale__mother_brand_id=brand_id)
            elif req_u_profile.role == USERS_ROLE.MANAGER:
                # shop limit for shop keeper
                shops_id = [s.id for s in req_u_profile.shops.all()]

                if req_u_profile.allow_internet_operate:
                    # extend global sales item for shop keeper
                    q = q & (Q(shop__in=shops_id) |
                             Q(sale__type_stock=TARGET_MARKET_TYPES.GLOBAL))
                else:
                    q = q & Q(shop__in=shops_id)

                q = q & Q(sale__mother_brand_id=brand_id)
            else:
                raise
        r = Incomes.objects.filter(q)
        sum = 0
        for income in r:
            sum += income.price * income.quantity
        return sum

class BaseOrdersView(StatsView):
    def _profile_limit(self, request):
        user = request.user
        q = Q()
        if not user.is_superuser:
            req_u_profile = user.get_profile()
            brand_id = req_u_profile.work_for
            if req_u_profile.role == USERS_ROLE.ADMIN:
                # brand limit for brand admin
                q = Q(brand_id=brand_id)
            elif req_u_profile.role == USERS_ROLE.MANAGER:
                # shop limit for shop keeper
                shops_id = [s.id for s in req_u_profile.shops.all()]

                if req_u_profile.allow_internet_operate:
                    # extend global sales item for shop keeper
                    q = (Q(shop_id__in=shops_id) |
                         Q(shop_id__isnull=True))
                else:
                    q = Q(shop_id__in=shops_id)
                q = q & Q(brand_id=brand_id)
            else:
                raise
        return q

    def _filter_out_orders(self, q):
        r = Orders.objects.filter(q)
        orders = set()
        for obj in r:
            orders.add(obj.order_id)
        return orders


    def _day_order(self, request, date):
        from_ = date
        to = date + timedelta(days=1)
        profile_limit = self._profile_limit(request)

        # get pending orders
        q = (Q(pending_date__isnull=False) &
             Q(pending_date__lt=to) &
             (Q(waiting_payment_date__isnull=True) |
              Q(waiting_payment_date__gte=to)
             ))
        q = q & profile_limit
        pending_orders = self._filter_out_orders(q)
        pending_count = len(pending_orders)

        # get waiting payment orders.
        q = (Q(waiting_payment_date__isnull=False) &
             Q(waiting_payment_date__lt=to) &
             (Q(waiting_shipping_date__isnull=True) |
              Q(waiting_shipping_date__gte=to)
             ))

        q = q&profile_limit
        waiting_payment_orders = self._filter_out_orders(q)
        waiting_payment_orders -= pending_orders
        waiting_payment_count = len(waiting_payment_orders)

        # get waiting shipping orders.
        q = (Q(waiting_shipping_date__isnull=False) &
             Q(waiting_shipping_date__lt=to) &
             (Q(completed_date__isnull=True) |
              Q(completed_date__gte=to))
        )
        q = q&profile_limit
        waiting_shipping_orders = self._filter_out_orders(q)
        waiting_shipping_orders -= waiting_payment_orders
        waiting_shipping_orders -= pending_orders
        waiting_shipping_count = len(waiting_shipping_orders)

        # get completed orders.
        q = (Q(completed_date__isnull=False) &
             Q(completed_date__lt=to) &
             Q(completed_date__gte=from_))

        q = q&profile_limit
        completed_orders = self._filter_out_orders(q)

        completed_orders -= waiting_shipping_orders
        completed_orders -= waiting_payment_orders
        completed_orders -= pending_orders
        completed_count = len(completed_orders)

        order_stats = {ORDER_STATUS.PENDING: pending_count,
                       ORDER_STATUS.AWAITING_PAYMENT: waiting_payment_count,
                       ORDER_STATUS.AWAITING_SHIPPING: waiting_shipping_count,
                       ORDER_STATUS.COMPLETED: completed_count,
                       }
        return order_stats

class StatsOrdersView(BaseOrdersView):
    def get(self, request, *args, **kwargs):
        week_days = self.gen_week_days()
        orders = []

        for date in week_days:
            order_status = self._day_order(request, date)
            orders.append([date.strftime(DT_FORMAT), order_status])

        print orders
        obj = {'pending': orders[0][1][ORDER_STATUS.AWAITING_SHIPPING],
               'lines': [[item[0], item[1][ORDER_STATUS.COMPLETED] + item[1][ORDER_STATUS.AWAITING_SHIPPING]]
                            for item in orders]}
        return HttpResponse(ujson.dumps(obj),
                            mimetype="application/json")


class StatsVisitorsView(BaseOrdersView):
    def get(self, request, *args, **kwargs):
        week_days = self.gen_week_days()

        orders = []
        ticks = []
        visitors_days_count = []
        for date in week_days:
            day_count = self._day_visitors(date)
            ticks.append(date.strftime(DT_FORMAT))
            visitors_days_count.append(day_count)

            order_status = self._day_order(request, date)
            orders.append([date.strftime(DT_FORMAT), order_status])

        cli = redis_cli(settings.SALES_SIM_REDIS)
        try:
            pong = cli.ping()
            if pong:
                visitors_online = cli.get("VISITORS_ONLINE")
            else:
                visitors_online = self._remote_visitors_online()
        except ConnectionError, e:
            logging.error('Failed to connect stats redis server')
            visitors_online = self._remote_visitors_online()

        trans_rate_line = []
        for index in range(len(orders)):
            order = orders[index][1]
            orders_count = order[ORDER_STATUS.COMPLETED] + order[ORDER_STATUS.AWAITING_SHIPPING]
            v_day_count = visitors_days_count[index]

            rate = 0
            if v_day_count > 0:
                rate = orders_count / v_day_count
            trans_rate_line.append(rate)

        ticks.reverse()
        visitors_days_count.reverse()
        trans_rate_line.reverse()


        obj = {'ticks': ticks,
               'visitors_online': visitors_online,
               'visitors_day_count': visitors_days_count,
               'trans_rate_line': trans_rate_line}
        return HttpResponse(ujson.dumps(obj),
                            mimetype="application/json")

    def _day_visitors(self, date):
        from_ = date
        to = date + timedelta(days=1)

        q = Q(visit_time__gte=from_) & Q(visit_time__lt=to)
        return Visitors.objects.filter(q).count()

    def _remote_visitors_online(self):
        try:
            url = settings.STATS_VISITORS_ONLINE
            data = get_from_remote(
                url,
                settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                settings.PRIVATE_KEY_PATH)
            visitors_online = ujson.loads(data)['count']
            return visitors_online
        except Exception, e:
            logging.error('remote_visitors_online_err:%s', e)
            return '-'
