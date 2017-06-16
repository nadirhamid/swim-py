
from .swim_client import SwimClient
from .swim_exceptions import SwimDisseminationFailedException
from .mesage_proc import MessageProc
from .mesage_proc_types import MessageProcTypes
from . import logger

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

        def determine_state():
           self.queue.put(MessageProc(MessageProcTypes.DISSEMINATION_UPDATES), MessageProcMember(member,pid))
           member = self.recv_queue.get()
           messages = member.get_message_queue()
           first_message = sorted(messages, cmp=message_sort)[0]
           return first_message.get_state()
         
        def refresh_member(state):
            memory_member.update(state)
            message = MessageProc(MessageProcTypes.UPDATE_MEMBER,memory_member)
            self.queue.put( message )

        def first_state_eval(state):
           state = determine_state(messages)
           refresh_member(state)
           if state == MemberStatus.SUSPECT:
              suspect_timeout()

        def suspect_timeout():
           logger.info("IN SUSPECT TIMEOUT FOR %s"%( member.connection_string(), ))
           time.sleep(SwimDefaults.SUSPECT_TIMEOUT)
           pid = os.getpid()
           state = determine_state()
           
           logger.info("REEVALUTED STATUS FOR %s IS %s"%(member.connection_string(), reeval_state,))
           self.queue.put( MessageProc(MessageProcTypes.DISSEMINATE,Message(
                   MessageTypes.UPDATE,
                   **dict(
                        destination=member.connection_string(),
                        state=state ) ) ))
        first_state_eval(eval_state)


    def send_update(self, message):
       logger.info("SENDING DISSEMINATION UPDATE")
       logger.info(message.get_type())
       self.queue.put(MessageProc(MessageProcTypes.MEMBERS))
       members = self.recv_queue.get()
       self.queue.put(MessageProc(MessageProcTypes.MEMBER_LOCAL_DISSEMINATE))
       local_member = self.recv_queue.get()
       message.set_incarnation( local_member.get_incarnation() )
       def try_update(member):
            try:
              logger.info("SENDING DISSEMINATION UPDATE TO %s"%(member.connection_string()))
              self.try_update(local_member, member, message)
            except SwimDissemninationFailedException:
              logger.info("SENDING DISSEMINATION FAILED FOR %s"%(member.connection_string()))
       try_update( local_member )
       for member in members:
            try_update( member )
    def start(self):
        while True:
           try:
              message =self.recv_queue.get()
              self.send_update(message)
           except Exception,ex:
              print_exc(ex)
        
            
