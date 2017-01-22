import os
import time

from celery import Celery
import redis
import requests

import status

db = redis.StrictRedis(decode_responses=True)
task_queue = Celery("tasks", broker=os.environ["CELERY_BROKER"])

@task_queue.task
def xdd_login(username, password):
    time.sleep(10)
    db.set("is_server_busy", "0")
    print("xdd_login(...) OK")
