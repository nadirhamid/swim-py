from .message_proc_types import MessageProcTypes

class MessageProcUpdate(object):
    type = MessageProcTypes.DISSEMINATION_UPDATE
    def __init__(self, member, message):
        self.member = member
        self.message = message
