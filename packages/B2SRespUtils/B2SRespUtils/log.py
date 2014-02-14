import logging

from logging import config as log_config

def setupLogging(config_file):
    log_config.fileConfig(config_file)
    logging.info('Logger (re)started')
    logging.debug('with debug logging enabled')
