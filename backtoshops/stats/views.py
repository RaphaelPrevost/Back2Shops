import ujson

from datetime import datetime, timedelta

from common.constants import USERS_ROLE
from common.constants import TARGET_MARKET_TYPES
from django.db.models import Q
from django.http import HttpResponse
from fouillis.views import OperatorUpperLoginRequiredMixin
from django.views.generic import View
from stats.models import Incomes, Orders

from B2SProtocol.constants import ORDER_STATUS

DT_FORMAT = "%Y-%m-%d"

class StatsView(OperatorUpperLoginRequiredMixin, View):
    def parse_params(self, request):
        from_ = request.GET.get('from')
        to = request.GET.get('to')

        if from_ is None and to is None:
            from_ = datetime.utcnow().date()
            to = datetime.utcnow().date() + timedelta(days=1)
        else:
            from_ = datetime.strptime(from_, DT_FORMAT)
            to = datetime.strptime(to, DT_FORMAT)
        return from_, to


class StatsIncomesView(StatsView):
    def get(self, request, *args, **kwargs):
        user = request.user
        from_, to = self.parse_params(request)

        # from_/to limit
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

        return HttpResponse(sum, mimetype="application/json")

class StatsOrdersView(StatsView):
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

    def get(self, request, *args, **kwargs):
        from_, to = self.parse_params(request)

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
        return HttpResponse(ujson.dumps(order_stats),
                            mimetype="application/json")

