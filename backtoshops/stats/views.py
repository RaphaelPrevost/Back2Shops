from datetime import datetime, timedelta

from common.constants import USERS_ROLE
from common.constants import TARGET_MARKET_TYPES
from django.db.models import Q
from django.http import HttpResponse
from fouillis.views import OperatorUpperLoginRequiredMixin
from django.views.generic import View
from stats.models import Incomes

DT_FORMAT = "%Y-%m-%d %H:%M:%S"
class StatsIncomesView(OperatorUpperLoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        from_ = request.GET.get('from')
        to = request.GET.get('to')

        if from_ is None and to is None:
            from_ = datetime.utcnow().date()
            to = datetime.utcnow().date() + timedelta(days=1)
        else:
            from_ = datetime.strptime(from_, DT_FORMAT)
            to = datetime.strptime(to, DT_FORMAT)

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
            else:
                raise
        r = Incomes.objects.filter(q)
        sum = 0
        for income in r:
            sum += income.price * income.quantity

        return HttpResponse(sum, mimetype="application/json")