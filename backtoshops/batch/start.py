import gevent
import signal
from batch.tasks_map import map
from gevent import Timeout

def batch_stop(task_list):
    print 'tasks will stops in 3 seconds ...'
    timeout = Timeout(3)
    timeout.start()
    try:
        gevent.wait(task_list)
    except Timeout:
        for task in task_list:
            task.kill()


def batch_start():
    tasks_obj = []

    for tasks in map.values():
        for task in tasks:
            tasks_obj.append(task())


    task_list = []
    for task in tasks_obj:
        task_list.append(gevent.spawn(task.run))

    gevent.signal(signal.SIGCHLD, batch_stop, task_list)
    gevent.signal(signal.SIGTERM, batch_stop, task_list)
    gevent.signal(signal.SIGINT, batch_stop, task_list)

    gevent.joinall(task_list)