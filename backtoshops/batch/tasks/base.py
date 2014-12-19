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
import gevent
import signal

class Task(object):
    help = None
    interval = None
    stopping = False
    stopping_sleep = 2
    lock = False

    def __init__(self):
        gevent.signal(signal.SIGINT, self.stop)
        gevent.signal(signal.SIGTERM, self.stop)
        gevent.signal(signal.SIGCHLD, self.stop)

    def run(self):

        if self.stopping:
            logging.info('STOPPING TASK: %s', self.help)
            print 'STOPPING TASK: %s' % self.help
            return

        logging.info('HANDLING TASK: %s', self.help)
        print 'HANDLING TASK: %s' % self.help

        try:
            self.handle()
            print '--HANDLED TASK: %s' % self.help
        finally:
            gevent.sleep(self.interval)
            self.run()

    def handle(self):
        raise NotImplementedError

    def stop(self):
        self.stopping = True
        gevent.sleep(self.stopping_sleep)