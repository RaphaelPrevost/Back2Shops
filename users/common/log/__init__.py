import settings
import logging

from logging import config as log_config

def setupLogging():
    log_config.fileConfig(settings.LOG_CONFIG_FILE)
    logging.info('Logger (re)started')
    logging.debug('with debug logging enabled')
