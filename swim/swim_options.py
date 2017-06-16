
from .swim_defaults import SwimDefaults
from .swim_exceptions import SwimOptionException
from .transport_serializer import TransportSerializer

class SwimOptionsBase(object):
    def __init__(self, opts=dict()):
        self.transport_serializer = opts.get("transport_serializer", TransportSerializer)

class SwimOptions(SwimOptionsBase):
    def __init__(self, opts=dict()):
        if not "hosts" in opts:
            raise SwimOptionException("Please specify hosts option")
        self.original = opts
        self.hosts = opts.get("hosts")
        self.local = opts.get("local", SwimDefaults.LOCAL)
        self.interval = opts.get("interval", SwimDefaults.INTERVAL)
        self.join_timeout = opts.get("join_timeout", SwimDefaults.JOIN_TIMEOUT)
        self.transport_serializer = opts.get("transport_serializer", TransportSerializer)
        SwimOptionsBase.__init__(self, opts)

    def get(self, option_name, default=None):
        if hasattr(self, option_name):
            return getattr( self, option_name )
        return default
