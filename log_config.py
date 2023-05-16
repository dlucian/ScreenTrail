import logging

def setup_logging():
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(filename='output.log', level=logging.DEBUG, format=log_format)
