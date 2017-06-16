from .swim_defaults import SwimDefaults
from .swim_client import SwimClient
from .swim_exceptions import SwimPingFailedException, SwimPingRequestFailedException
from .swim_failure_options import SwimFailureOptions
from .member_status import MemberStatus
from .message_types import MessageTypes
from .message import Message
from .message_proc_types import MessageProcTypes
from .message_proc import MessageProc

from .failure_sequence import FailureSequence
from . import logger
from traceback import print_exc
import time

class FailureCheck(SwimClient):
   def __init__(self, opts):
       self.opts = SwimFailureOptions(opts)

   def try_a_ping(self, ping_candidate):
       try:
           self.do_request(ping_candidate, Message(MessageTypes.PING), 
                    timeout=self.opts.ping_timeout)
       except Exception,ex: ## A socket exception
         raise SwimPingFailedException()

   def routine_ping(self, ping_candidate):
       received_ack[ 0 ] = False
       def try_relay(relay_member):
         try:
            self.relay_ping_request( relay_member, ping_candidate )
            received_ack[ 0 ] = True
         except SwimPingRequestFailedException,ex:
            ## DESTINATION did not respond. mark as suspect
            logger.info("PING REQUEST FAILED FROM HOST %s TO CANDIDATE %s"%( relay_member.connection_string(), ping_candidate.connection_string(), ) )
       def verify_ack():
          if received_ack[ 0 ]:
            self.mark_as(ping_candidate, MemberStatus.ALIVE)
          else:
            self.mark_as(ping_candidate, MemberStatus.SUSPECT)

       def loop_relay():
            ## try to relay
            logger.info("RELAYING PING TO OTHER MEMBERS")
            self.queue.put(MessageProc(MessageProcTypes.RELAY_MEMBERS))
            relay_members = self.recv_queue.get()
            logger.info("RELAY MEMBERS RECEIVED")
            for relay_member in relay_members:
                try_relay(relay_member)
                if received_ack:
                    break
            verify_ack()
       try:
            self.try_a_ping(ping_candidate)
       except SwimPingFailedException,ex:
            logger.info("PING FAILED FOR HOST: %s"%( ping_candidate.connection_string(), ))
            loop_relay()
   def routine_ping_request(self,origin,ping_candidate):
        ## DESTINATION responded send an Ack to the origin
        def report_to_origin():
            self.do_request(origin,
               Message(MessageTypes.ACK) )
        try:
            self.try_a_ping(ping_candidate)
            report_to_origin()
        except SwimPingFailedException,ex:
            logger.info("PING FAILED FOR HOST: %s"%( ping_candidate.connection_string(), ))

   def relay_ping_request(self, ping_request_candidate, ping_candidate):
        try:
           self.do_request(
            ping_request,
            Message(MessageTypes.PING_REQUEST,
                dict(
                    destination=ping_candidate.connection_string()
                )
            ),
            timeout=self.opts.ping_request_timeout
           )
        except Exception,ex:
            ##rethrow the DESTINATION did not respond
            raise SwimPingRequestFailedException()
   def mark_as(self, ping_candidate, status):
       ping_candidate.set_state( status )
       logger.info("UPDATING LOCAL MEMBERSHIP QUEUE")
       self.queue.put(
            MessageProc(MessageProcTypes.UPDATE_MEMBER_START,
                ping_candidate ) )
   def mark_as_suspect(self, ping_candidate):
        self.mark_as(ping_candidate, MemberStatus.SUSPECT)

   def mark_as_alive(self, ping_candidate):
        self.mark_as(ping_candidate, MemberStatus.ALIVE)


   def start(self):
       while True:
           logger.info("FETCHING NEXT CANDIDATE FOR FAILURE DETECTION")
           self.queue.put(MessageProc(MessageProcTypes.NEXT_CANDIDATE))
           ping_candidate = self.recv_queue.get()
           logger.info("PINGING CANDIDATE %s"%(ping_candidate.connection_string()))
           self.routine_ping( ping_candidate )
           ping_candidate.set_tried(True)
           time.sleep( self.opts.ping_timeout )
