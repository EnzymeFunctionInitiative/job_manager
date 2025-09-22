# app/job_logger.py

from typing import Tuple
import logging
import logging.handlers
from enum import Enum

class logger_names(str, Enum):
    """
    String Enum to contain the names for the various loggers used.
    Names/strings follow the expected magic naming of parent.child names. In
    this regard, job_manager is the parent logger with children loggers for
    each module that gets called.
    """
    MAIN = "job_manager"
    PLUGIN_LOADER = "job_manager.plugin_loader"
    DATABASE = "job_manager.database"
    JOB_HANDLER = "job_manager.job_handler"
    CONNECTOR = "job_manager.connector"

def setup_logger(
        name,
        log_file,
        file_level=logging.DEBUG,
        console_level=logging.WARNING
    ) -> logging.Logger:
    """
    Set up as a logging manager that writes to file and to stdout. Only used to
    set up the logger_names.MAIN logger, all children loggers propagate their
    log events to the parent logger.
    """
    # create the logger, which can control multiple streams for the logged
    # messages
    logger = logging.getLogger(name)
    logger.setLevel(file_level)

    # create a file handler that will write logging messages out to a file
    file_handler = logging.FileHandler(
        log_file,
        mode = "a"
    )
    #file_handler = logging.handlers.TimedRotatingFileHandler(
    #    log_file,
    #    mode = "a",
    #    when = "W6",
    #    backupCount=14
    #)
    file_handler.setLevel(file_level)

    # create a console stream of logging messages, use a higher log level to
    # avoid overflowing the console
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(console_level)

    # create a uniform format for both handlers to use
    formatter = logging.Formatter(
        '{asctime}\t\t{levelname} {module:>15}({lineno}):\t{message}',
        style = "{" # specifically use {}-formatted or str.format() style
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # add both file_ and stream_ handlers to the logger to manage
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

def clean_logger(logger):
    """ Clean up the logger's handler instances once we are done with them. """
    for handle in logger.handlers:
        handle.flush()
        handle.close()
        logger.removeHandler(handle)


