
from .member_list import MemberList
from .member import Member
from .member_status import MemberStatus
from .message_proc import MessageProc
from .message_proc_types import MessageProcTypes
from .message_proc_member  import MessageProcMember
from .swim_defaults import SwimDefaults
from . import logger
from random import shuffle, choice
import os
import time
import socket
class Membership(MemberList):
    def __init__(self, opts):
        MemberList.__init__(self, opts.get("hosts"))
        self.opts = opts
    def get_members(self):        
        return self.members
    def get_candidates(self):
        def filter_fn(member):
            if not (member.tried):
                return True
            return False
        candidates = filter( filter_fn, self.get_members() )
        return candidates

    def update(self, member):
        logger.info("MEMBERSHIP UPDATE START FOR: %s"%(member.connection_string()))
        memory_member = self.from_host_and_port(member.get_host(), member.get_port())
        eval_state = member.get_state()
        def refresh_member(state):
            memory_member.update(state)
            message = MessageProc(MessageProcTypes.UPDATE_MEMBER,member)
            self.queue.put( message )
        def suspect_timeout():
           logger.info("IN SUSPECT TIMEOUT FOR %s"%( member.connection_string(), ))
           time.sleep(SwimDefaults.SUSPECT_TIMEOUT)
           pid = os.getpid()
           self.queue.put(MessageProc(MessageProcTypes.MEMBER), MessageProcMember(member,pid))
           member = self.recv_queue.get()
           reeval_state = member.get_state()
           logger.info("REEVALUTED STATUS FOR %s IS %s"%(member.connection_string(), reeval_state,))
           if ( reeval_state == eval_state ) and ( eval_state == MemberStatus.SUSPECT ):
             ## it has failed
             refresh_member(MemberStatus.FAULTY)

        if member.get_state()!=memory_member.get_state():
            refresh_member(eval_state)
            suspect_timeout()
    def sync(self, data):
        def map_destination( destination ):
           host_string = destination.split(":")
           return Member( host_string[ 0 ], host_string[ 1 ] ) 

        hosts = data['hosts']
        self.members = self.members + map(map_destination, hosts)

    def from_host_and_port(self, host, port):
        def filter_fn(member):
            if member.get_host() == host and member.get_port() == port:
                return True
            return False
        members_found = filter( filter_fn, self.get_members() )
        return members_found[ 0 ]
    def from_socket(self, socket):
        hostname = socket.gethostname()
        return self.from_host_and_port(hostname[0], int(hostname[1]))
    def from_connection_string(self, connection_string):
        splitted = connection_string.split(":")
        return self.from_host_and_port(splitted[0], int(splitted[1]))
    def next_candidate(self):
        candidates_available = self.get_candidates()
        if not len( candidates_available ) > 0:
            candidates_available = self.shuffle()
        candidate = candidates_available[ 0 ]
        candidate.set_tried( True )
        return candidate
    def fetch_relay_members(self, ping_candidate):
        amount_of_random = self.opts.get("ping_req_group_size")
        random_members = []
        for_member = self.from_host_and_port(ping_candidate.get_host(), ping_candidate.get_port())
        members = self.get_members()[:]
        members.remove(for_member)
        while (len( random_members ) != amount_of_random) and ( len( members ) > 0 ):
            a_choice = choice(members)
            random_members.append( a_choice )
            members.remove(a_choice)
        return random_members
        
    def set_members(self, members):
        self.members = members
    def shuffle(self):
        members = self.get_members()
        for member in members:
            member.set_tried(False)
        shuffle( members )
        return members
