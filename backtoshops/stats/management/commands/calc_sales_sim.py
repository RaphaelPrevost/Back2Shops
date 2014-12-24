# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
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
import math
import settings
import ujson

from collections import defaultdict
from stats.models import BoughtHistory
from stats.management.commands._base import StatsCommand
from B2SUtils.redis_cli import redis_cli


class Command(StatsCommand):
    help = "Calculate sales similarity and save the results into redis"

    def calc_smi(self, users_x, users_y):
        users_x = ujson.loads(users_x)
        users_y = ujson.loads(users_y)

        users_inter = set(users_x).intersection(users_y)
        if len(users_inter) == 0:
            return 0

        users_union = set(users_x).union(set(users_y))

        vector_x = [1 if u in users_x else 0 for u in users_union]
        vector_y = [1 if u in users_y else 0 for u in users_union]

        vector_index = range(len(users_union))

        # calculate similarity accroding with Cosine_similarity
        # refs: http://en.wikipedia.org/wiki/Cosine_similarity
        XY = [vector_x[i] * vector_y[i] for i in vector_index]
        XY = sum(XY)

        XX = [vector_x[i] * vector_x[i] for i in vector_index]
        YY = [vector_y[i] * vector_y[i] for i in vector_index]
        XX = sum(XX)
        YY = sum(YY)

        sim = float(XY) / (math.sqrt(XX) * math.sqrt(YY))
        return sim

    def handle(self, *args, **options):
        try:
            histories = BoughtHistory.objects.all()
            done_mark = defaultdict(dict)
            cli = redis_cli(settings.SALES_SIM_REDIS)

            for hist_x in histories:
                sale_x = hist_x.sale_id
                for hist_y in histories:
                    sale_y = hist_y.sale_id

                    if sale_y == sale_x:
                        continue
                    if done_mark[sale_x].get(sale_y) is not None:
                        continue

                    sim = self.calc_smi(hist_x.users, hist_y.users)
                    done_mark[sale_x][sale_y] = sim
                    done_mark[sale_y][sale_x] = sim

                    if sim > 0:
                        cli.zadd(sale_x, sale_y, sim)
                        cli.zadd(sale_y, sale_x, sim)

        except Exception, e:
            logging.error('calc_sales_sim_err: %s', e, exc_info=True)
