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