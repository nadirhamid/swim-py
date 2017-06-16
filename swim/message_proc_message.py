 
from .message_proc_types import MessageProcTypes
class MessageProcMessage(object):
    type = MessageProcTypes.MEMBER_MESSAGE
    def __init__(self, member, message):
        self.member = member
        self.message = message
         
        
