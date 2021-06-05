import logging
from logging.handlers import RotatingFileHandler
import os


def set_up_logging(loglevel=logging.DEBUG, saveLogFiles=True, saveLogFolder='logs', maxBytes=100000, backupCount=10):
    """
    Set up logging for dequa bot.
    :param loglevel: loglevel for the nky_util loggers
    :param saveLogFiles: if True adds the rotating file handler
    :param saveLogFolder: folder where to save the log files
    :param maxBytes: maximum size of each log file
    :param backupCount: maximum number of log files
    :return: the logger object
    """
    logger = logging.getLogger('dequa_bot')
    logger.handlers.clear()
    logger.setLevel(loglevel)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(name)s:%(filename)s:%(lineno)d] [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if saveLogFiles:
        if not os.path.exists(saveLogFolder):
            os.mkdir(saveLogFolder)
        logfile = os.path.join(saveLogFolder, 'dequa_bot.log')
        file_handler = RotatingFileHandler(logfile, maxBytes=maxBytes, backupCount=backupCount)
        formatter = logging.Formatter('[%(asctime)s] [%(name)s:%(filename)s:%(lineno)d] [%(levelname)s] %(message)s')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(loglevel)
        logger.addHandler(file_handler)
    return logger
