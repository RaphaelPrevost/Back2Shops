# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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
