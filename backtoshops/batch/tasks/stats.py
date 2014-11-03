import logging
from datetime import datetime, timedelta

from batch.tasks.base import Task
from django.core import management


class _BaseStatsTask(Task):
    cmd = None
    cmd_args = []
    cmd_options = {}
    def handle(self):
        try:
            management.call_command(self.cmd,
                                    *self.cmd_args,
                                    **self.cmd_options)
        except Exception, e:
            logging.error("task_running_err: %s", e, exc_info=True)


class CalcSalesSim(_BaseStatsTask):
    interval = 24 * 3600
    cmd = "calc_sales_sim"
    help = "calculate similarity between sales items"


class StatsBoughtHistory(_BaseStatsTask):
    interval = 3600
    cmd = 'stats_bought_history'
    help = ("fetch bought history from user server, "
            "data will be used to calculate sales similarity ")


class StatsVisitorsOnline(_BaseStatsTask):
    interval = 60
    cmd = 'stats_visitors_online'
    help = "fetch visitors online info from user server"


class _BaseStatsWeekDataTask(_BaseStatsTask):
    def handle(self):
        td = datetime.utcnow().date()
        from_ = td - timedelta(days=7)
        tm = td + timedelta(days=1)
        self.cmd_options = {'from': from_, 'to': tm}
        super(_BaseStatsWeekDataTask, self).handle()


class StatsIncomes(_BaseStatsWeekDataTask):
    interval = 600
    cmd = 'stats_incomes'
    help = "fetch incomes log from user server"


class StatsOrders(_BaseStatsWeekDataTask):
    interval = 3600
    cmd = 'stats_orders'
    help = "fetch orders log from user server"


class StatsVisitors(_BaseStatsWeekDataTask):
    interval = 1800
    cmd = 'stats_visitors'
    help = "fetch visitors log from user server"
