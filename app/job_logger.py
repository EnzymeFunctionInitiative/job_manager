
from typing import Tuple
import logging
import logging.handlers

def setup_logger(
        name,
        log_file,
        file_level=logging.DEBUG,
        console_level=logging.ERROR
    ) -> logging.Logger:
    """ Set up as a logging manager that writes to file and to stdout. """
    # create the logger, which can control multiple streams for the logged
    # messages
    logger = logging.getLogger(name)
    logger.setLevel(file_level)
    
    # create a file handler that will write logging messages out to a file
    file_handler = logging.handlers.FileHandler(
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
    stream_handler = logging.handlers.StreamHandler()
    stream_handler.setLevel(console_level)

    # create a uniform format for both handlers to use
    formatter = logging.Formatter(
        '{asctime}\t\t{levelname}\t{module}({lineno})\t\t{message}:',
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


