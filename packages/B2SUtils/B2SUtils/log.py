# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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
import traceback
import urllib
import urllib2

from logging import config as log_config

def setupLogging(config_file):
    log_config.fileConfig(config_file)
    logging.info('Logger (re)started')
    logging.debug('with debug logging enabled')

def addBugzScoutHandler(**bugz_scout_settings):
    handler = BugzScoutLogHandler(**bugz_scout_settings)
    handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(handler)


class BugzScoutLogHandler(logging.Handler):
    def __init__(self, url=None, user_name=None, project=None, area=None):
        logging.Handler.__init__(self)
        self.url = url
        self.username = user_name
        self.project = project
        self.area = area

    def emit(self, record):
        brief = '%s: %s' % (record.levelname, record.getMessage())
        brief = brief.replace('\n', '\\n').replace('\r', '\\r')

        if record.exc_info:
            stack_trace = '\n'.join(traceback.format_exception(*record.exc_info))
        else:
            stack_trace = 'No stack trace available'

        bug = {
            'ScoutUserName': self.username,
            'ScoutProject': self.project,
            'ScoutArea': self.area,
            'Description': brief,
            'Extra': stack_trace,
        }
        if self.url:
            urllib2.urlopen(self.url, urllib.urlencode(bug))

