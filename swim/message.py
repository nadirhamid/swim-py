import time
from . import destination_to_host_port

class Message(dict):
    def __init__(self, message_type, **kwargs):
         needed_data = dict( type = message_type )
         meta_data = dict(meta=dict( kwargs.items() + dict( time=time.time() ).items() ))
         dict_data = dict( needed_data.items() + meta_data.items() )
         if "destination" in kwargs:
            self.destination_host, self.destination_port = destination_to_host_port( kwargs['destination'] )
         dict.__init__(self, **dict_data)
    def get_meta_key(self, key):
        return self.get("meta").get(key)
    def get_time(self):
        return self.get_meta_key("time")
    def get_destination(self):
        return self.get_meta_key("destination")
    def get_destination_host(self):
        return self.destination_host
    def get_destination_port(self):
        return self.destination_port
    def get_state(self):
        return self.get_meta_key("state")
    def get_type(self):
        return self.get("type")
    @staticmethod
    def from_dict(a_dict):
        return Message(
            a_dict.get("type"),
            **a_dict.get("meta") )
