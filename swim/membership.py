
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
    def __init__(self, member_local, opts):
        MemberList.__init__(self, opts.get("hosts"))
        self.member_local = member_local
        self.opts = opts

    def add_member_if_needed(self, member):
        current_member = self.from_host_and_port(member.get_host(), member.get_port())
        local_member = self.get_member_local()
        if current_member is None and not local_member.matches(member):
           self.members.append(member)
       
    def get_members(self):        
        return self.members
    def get_member_local(self):
        return self.member_local
    def get_candidates(self):
        def filter_fn(member):
            if not (member.tried):
                return True
            return False
        candidates = filter( filter_fn, self.get_members() )
        return candidates
    def from_host_and_port(self, host, port):
        def filter_fn(member):
            if member.get_host() == host and member.get_port() == port:
                return True
            return False
        members_found = filter( filter_fn, self.get_members() )
        if len( members_found ) > 0:
          return members_found[ 0 ]
    def from_socket(self, socket):
        hostname = socket.gethostname()
        return self.from_host_and_port(hostname[0], int(hostname[1]))
    def from_connection_string(self, connection_string):
        splitted = connection_string.split(":")
        return self.from_host_and_port(splitted[0], int(splitted[1]))
    def next_candidate(self):
        members = self.get_members()
        if not len( members ) > 0:
            return
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
    def update_member(self, updated_member):
        memory_member = self.from_host_and_port(updated_member.get_host(),updated_member.get_port())
        memory_member.update( updated_member.get_state() )
