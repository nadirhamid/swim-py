import logging
import time

logging.basicConfig(filename='swim.log', level=logging.INFO)
logger = logging.getLogger("swim.log")
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)


def make_connection_string(host, port):
    return ":".join([ host, str( port ) ])
def destination_to_host_port(destination):
    splitted = destination.split(":")
    return [ splitted[0], int( splitted[1] ) ]

