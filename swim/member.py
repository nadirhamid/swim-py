
from . import make_connection_string
from .member_status import MemberStatus
from . import logger
import time

class Member(object):
   def __init__(self, host="", port=0, tried=False):
      self.host = host
      self.port = int( port )
      self.tried = tried
      ## until determined
      self.state = None
      self.incarnation = 0
   def connection_string(self):
      return make_connection_string(self.host, self.port)
   def get_host(self):
      return self.host
   def get_last_updated(self):
      return self.last_updated
   def get_port(self):
      return self.port
   def get_state(self):
      return self.state
   def get_tried(self):
      return self.tried
   def set_host(self, host):
       self.host = host
   def set_port(self, port):
       self.port = port
   def set_state(self, state):
       self.state
   def set_tried(self, tried):
      self.tried = tried
   def increment_incarnation(self):
      self.incarnation += 1
   def update(self,state):
        logger.info("SETTING %s's STATE TO %s"%( self.connection_string(), state, ) )
        self.set_state( state )

