import ujson
import feedparser
import gevent
import logging
import settings

from bs4 import BeautifulSoup


class FetchCoinFeed(object):
    ttl = 24 * 3600

    def run(self):
        self.fetch()
        gevent.spawn_later(self.ttl, self.run)

    def fetch(self):
        try:
            logging.info('start fetch dragon dollar feed ...')
            feed = feedparser.parse("http://www.dragondollar.com/coins/feed/")
            logging.info('fetched dragon dollar feed: %s', feed)
            coins = feed['entries'][:2]
            cache = []
            for coin in coins:
                content = coin.content[0].value
                soup = BeautifulSoup(content)
                img = soup.find_all('img')[0]

                cache.append(
                    {'title': coin.title,
                     'link': coin.link,
                     'summary': coin.summary,
                     'img': {'src': img.attrs['src'],
                             'alt': img.attrs['alt']}
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

