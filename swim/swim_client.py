import socket
import time
from select import select
from .swim_defaults import SwimDefaults
from . import logger
class SwimClient(object):
   def __init__(self):
        pass
   def send_with_socket(self,sock,packet,timeout=3,recv=True):
        data = self.opts.transport_serializer.dumps( packet )
        logger.info("SENDING REQUEST %s"%(data,))
        sock.send(data)
        if recv:
            logger.info("TRYING TO RECEIVE RESPONSE FROM SOCKET")
            ready = select([sock], [], [], timeout)
            if ready[ 0 ]:
               response = sock.recv(SwimDefaults.BUFFER_SIZE)
            logger.info("RECEIVED RESPONSE %s"%(response,))
        sock.close()
   def send(self,member,packet,timeout=3,recv=True):
       sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       sock.settimeout(timeout)
       sock.connect((member.get_host(), member.get_port(),))
       self.send_with_socket(sock,packet,recv=recv)
