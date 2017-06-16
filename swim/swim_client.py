import socket
import time
from .swim_defaults import SwimDefaults
from . import logger
class SwimClient(object):
   def __init__(self):
        pass
   def do_request(self,member,packet,timeout=3,recv=True):
        data = self.opts.transport_serializer.dumps( packet )
        logger.info("SENDING REQUEST %s"%(data,))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((member.get_host(), member.get_port(),))
        sock.send(data)
        if recv:
            response = sock.recv(SwimDefaults.BUFFER_SIZE)
            logger.info("RECEIVED RESPONSE %s"%(response,))
        sock.close()
