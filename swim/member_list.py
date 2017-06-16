
from .member import Member

class MemberList(object):
    def __init__(self, hosts=[]):
        def map_fn( host ):
            splitted = host.split(":")
            return Member( splitted[0], splitted[ 1 ] )
        self.members = map(map_fn, hosts)
