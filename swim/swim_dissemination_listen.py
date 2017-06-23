
from .swim_client import SwimClient
from .swim_exceptions import SwimDisseminationFailedException
from .message_proc import MessageProc
from .message_proc_types import MessageProcTypes
from traceback import print_exc
from . import logger
import time

class SwimDisseminationListen(SwimClient):
    def __init__(self, opts):
       self.opts = opts
       ## pool 
       self.attempts_to_update = []
    def try_update(self, local_member, member, message):
        try:
            self.send(member,message)
        except Exception,ex:
            raise SwimDisseminationFailedException()
    def send_update(self, packet):
       message = packet.message
       logger.info(message.get_type())
       members = packet.members
       local_member = packet.member_local
       message.set_incarnation( local_member.get_incarnation() )
       def try_update(member):
            try:
              self.try_update(local_member, member, message)
            except SwimDisseminationFailedException, ex:
              print_exc(ex)
            time.sleep( self.opts.dissemination_timeout )
       try_update( local_member )
       for member in members:
            try_update( member )
    def start(self):
        while True:
           try:
              packet =self.recv_queue.get()
              self.send_update(packet)
           except Exception,ex:
              print_exc(ex)
        
            
