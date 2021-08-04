import os
from shutil import copyfile

from django.apps import AppConfig
import logging
from leadsapi.settings import BASE_DIR

logger = logging.getLogger("Startup")

def startup():
    logger.info('Performing database restore..')
    DB_FILE = os.path.join(BASE_DIR, 'db.sqlite3')
    DB_RESTORE_FILE = os.path.join(BASE_DIR, 'db.sqlite3.restore')
    if os.path.exists(DB_FILE):
        copyfile(DB_FILE, DB_RESTORE_FILE)
    else:
        logger.info('No restore changes detected!')


class MyAppConfig(AppConfig):
    name = 'restapi'
    verbose_name = "My Application"

    def ready(self):
        if os.environ.get('RUN_MAIN'):
            startup()
