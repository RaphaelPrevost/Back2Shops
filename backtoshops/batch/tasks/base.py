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