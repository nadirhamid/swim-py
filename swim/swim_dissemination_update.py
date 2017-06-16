
from .swim_client import SwimClient
from .swim_exceptions import SwimDisseminationFailedException
from .mesage_proc import MessageProc
from .mesage_proc_types import MessageProcTypes
from . import logger

class SwimDisseminationUpdate(object):
    def __init__(self, opts):
       self.opts = opts
    def update_member(self, member):
        logger.info("MEMBERSHIP UPDATE START FOR: %s"%(member.connection_string()))
        memory_member = self.from_host_and_port(member.get_host(), member.get_port())
        eval_state = member.get_state()
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
            self.recv_queue.put(MessageProc(MessageProcTypes.DISSEMINATION_CLEAR, member))
        def determine_state_before():
           self.queue.put(MessageProc(MessageProcTypes.DISSEMINATION_UPDATES), MessageProcMember(member,pid))
           member = self.recv_queue.get()
           messages = member.get_message_queue()
           first_message = sorted(messages, cmp=message_sort)[0]
           return first_message.get_state()
        def determine_state_after():
           state = determine_state_before()
           if  ( state ==  MemberStatus.SUSPECT ):
              state = MemberStatus.CONFIRM
           return state
           
         
        def refresh_member(state):
            memory_member.update(state)
            message = MessageProc(MessageProcTypes.UPDATE_MEMBER,memory_member)
            self.queue.put( message )

        def first_state_eval(state):
           state = determine_state_before()
           refresh_member(state)
           if state == MemberStatus.CONFIRM:
              self.queue.send(MessageProc(MessageProcTypes.MEMBER_FAULTY, member))
              update_end()
           else:
               logger.info("IN SUSPECT TIMEOUT FOR %s"%( member.connection_string(), ))
               time.sleep(SwimDefaults.SUSPECT_TIMEOUT)
               pid = os.getpid()
               state = determine_state_after()
               logger.info("REEVALUTED STATUS FOR %s IS %s"%(member.connection_string(), reeval_state,))
               self.queue.put( MessageProc(MessageProcTypes.DISSEMINATE,Message(
                       MessageTypes.UPDATE,
                       **dict(
                            destination=member.connection_string(),
                            state=state ) ) ))
        first_state_eval(eval_state)
            
