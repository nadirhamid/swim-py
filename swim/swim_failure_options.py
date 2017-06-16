from .swim_options import SwimOptionsBase
from .swim_defaults import SwimDefaults
class SwimFailureOptions(SwimOptionsBase):
   def __init__(self, opts):
       self.ping_timeout = opts.get("ping_timeout", SwimDefaults.PING_TIMEOUT)
       self.ping_req_timeout = opts.get("ping_req_timeout", SwimDefaults.PING_REQ_TIMEOUT)
       self.ping_req_group_size = opts.get("ping_req_group_size", SwimDefaults.PING_REQ_GROUP_SIZE)
       SwimOptionsBase.__init__(self, opts)


