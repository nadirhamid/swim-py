import time
import uuid

class MessageProc(object):
    def __init__(self, message_type, data=None):
        self.type = message_type
        self.data = data
        self.id = str( uuid.uuid4() )
