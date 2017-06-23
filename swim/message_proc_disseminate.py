from .message_proc_types import MessageProcTypes

class MessageProcDisseminate(object):
    type = MessageProcTypes.DISSEMINATE
    def __init__(self, member, message, member_local=None, members=[]):
        self.member = member
        self.message = message
        self.member_local = member_local
        self.members = members
