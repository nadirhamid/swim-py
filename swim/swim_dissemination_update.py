
from .swim_client import SwimClient
from .swim_exceptions import SwimDisseminationFailedException
from .swim_dissemination_member import SwimDisseminationMember
from .message_proc import MessageProc
from .message_proc_disseminate import MessageProcDisseminate
from .message_proc_types import MessageProcTypes
from .message import Message
from .message_types import MessageTypes

from .member_status import MemberStatus
from . import logger
import os
import time

class SwimDisseminationUpdate(object):
    def __init__(self, opts):
       self.opts = opts
    def update(self, memory_member, message):
        logger.info("MEMBERSHIP UPDATE START FOR: %s"%(memory_member.connection_string()))
        eval_state = message.get_state()
        proc_member = SwimDisseminationMember(memory_member, os.getpid())
        def message_sort(message_a, message_b):
            state_a = message_a.get_state() 
            incarnation_a = message_a.get_incarnation()
            state_b = message_b.get_state() 
            incarnation_b = message_b.get_incarnation()
            if ( state_a == MemberStatus.CONFIRM ):
                return -1
            if (  ( state_a == MemberStatus.ALIVE and state_b == MemberStatus.SUSPECT ) and ( incarnation_a > incarnation_b ) ):
                return -1
            if (  ( state_a == MemberStatus.SUSPECT and state_b == MemberStatus.ALIVE ) and ( incarnation_a > incarnation_b ) ):
                return -1
            return 1

        def update_end():
           self.queue.put(MessageProc(MessageProcTypes.DISSEMINATION_CLEAR, proc_member))
        def determine_state_before():
           self.queue.put(MessageProc(MessageProcTypes.DISSEMINATION_UPDATES, proc_member))
           messages = self.recv_queue.get()
           first_message = sorted(messages, cmp=message_sort)[0]
           return first_message.get_state()
        def determine_state_after():
           state = determine_state_before()
           if  ( state ==  MemberStatus.SUSPECT ):
              state = MemberStatus.CONFIRM
           return state
           
         
        def refresh_or_exit(state):
            message = MessageProc(MessageProcTypes.DISSEMINATION_VALID,proc_member)
            self.queue.put( message )
            valid = self.recv_queue.get()
            if not valid:
                logger.info("DISSEMINATION ON %s IS NO LONGER VALID. EXITING DISSEMINATION PROCESS %s"%(memory_member.connection_string(),os.getpid()))
                exit( 1 )

            memory_member.update(state)
            message = MessageProc(MessageProcTypes.UPDATE_MEMBER,memory_member)
            self.queue.put( message )

        def first_state_eval(state):
           state = determine_state_before()
           logger.info("EVALUTED STATUS FOR %s IS %s"%(memory_member.connection_string(), state,))
           refresh_or_exit(state)
           def do_suspect_timeout_if_needed():
               if state == MemberStatus.SUSPECT:
                   logger.info("IN SUSPECT TIMEOUT FOR %s"%( memory_member.connection_string(), ))
                   time.sleep(self.opts.suspect_timeout)
           if state == MemberStatus.CONFIRM:
              self.queue.put(MessageProc(MessageProcTypes.FAULTY_MEMBER, memory_member))
              update_end()
           else:
               do_suspect_timeout_if_needed()
               state = determine_state_after()
               refresh_or_exit(state)
               logger.info("REEVALUTED STATUS FOR %s IS %s"%(memory_member.connection_string(), state,))
               self.queue.put( MessageProcDisseminate(
                       memory_member,
                       Message(
                           MessageTypes.UPDATE,
                           **dict(
                                destination=memory_member.connection_string(),
                                state=state ) ) ))
        first_state_eval(eval_state)
            
