import os
import time

from celery import Celery
import requests

task_queue = Celery("tasks", broker=os.environ["CELERY_BACKEND"])

@task_queue.task
def xdd_login(username, password):
    time.sleep(15)
    print("xdd_login(...) OK")
