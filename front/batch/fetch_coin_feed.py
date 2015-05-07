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


import ujson
import feedparser
import gevent
import logging
import settings
import HTMLParser



class FetchCoinFeed(object):
    ttl = 24 * 3600

    def run(self):
        self.fetch()
        gevent.spawn_later(self.ttl, self.run)

    def fetch(self):
        try:
            logging.info('start fetch dragon dollar feed ...')
            feed = feedparser.parse("http://%s/coins/feed/"
                                    % settings.DRAGON_BLOG_ADDR)
            logging.info('fetched dragon dollar feed: %s', feed)
            coins = feed['entries'][:2]
            cache = []
            for coin in coins:
                content = coin.content[0].value
                summary = HTMLParser.HTMLParser().unescape(coin.summary)

                cache.append(
                    {'title': coin.title,
                     'link': coin.link,
                     'summary': summary,
                     'media': {'url': coin.media_content[0]['url'],
                               'medium': coin.media_content[0]['medium']}
                     }
                )

            self._write_local_cache(cache)
        except Exception, e:
            logging.error('Server Error: %s', (e,), exc_info=True)

        logging.info('finished fetch dragon dollar feed')


    def _write_local_cache(self, cache):
        try:
            with open(settings.DRAGON_FEED_CACHE_PATH, 'w') as f:
                ujson.dump(cache, f)
        except IOError, e:
            logging.error("Failed to write %s: %s",
                          (settings.DRAGON_FEED_CACHE_PATH, e),
                          exc_info=True)
        except Exception, e:
            logging.error('Server Error: %s', (e,), exc_info=True)

        gevent.sleep(1)

