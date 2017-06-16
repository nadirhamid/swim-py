import time

class MessageProc(object):
    def __init__(self, message_type, data=None):
        self.type = message_type
        self.data = data
