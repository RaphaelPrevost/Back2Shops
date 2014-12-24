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


import settings
import signal
import subprocess

from django.core.management.base import BaseCommand


redis_conf = """
port %(port)s
timeout 60
dbfilename sales_sim_%(port)s.rdb
pidfile redis-server-%(port)s.pid
loglevel debug
logfile sales_sim_%(port)s.log
save 900 1
save 300 10
save 60 10000
dir ./
unixsocket /tmp/redis.sock
unixsocketperm 777
"""

class Command(BaseCommand):

    def handle(self, *args, **options):
        server = None
        def exit(sig, *arg):
            if sig == signal.SIGCHLD:
                print 'redis-server down, exit'
            elif server:
                server.terminate()
                server.wait()

        signal.signal(signal.SIGINT, exit)
        signal.signal(signal.SIGTERM, exit)
        signal.signal(signal.SIGCHLD, exit)

        r_conf = redis_conf % {'port': settings.SALES_SIM_REDIS['PORT']}
        server = subprocess.Popen(['redis-server', '-'],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        server.stdin.write(r_conf)
        server.stdin.close()

        try:
            server.wait()
        except Exception, e:
            server.terminate()
            print e