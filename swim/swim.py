
from .failure_check import FailureCheck
from .membership import Membership
from .swim_exceptions import SwimException
from .swim_defaults import SwimDefaults
from .swim_server import SwimServer
from .swim_server_handler import SwimServerHandler
from .swim_status import SwimStatus
from .swim_options import SwimOptions
from .transport_serializer import TransportSerializer
from .message_proc import MessageProc
from .message_proc_types import MessageProcTypes
from .membership_process import MembershipProcess
from . import logger
from .base import Base
from multiprocessing import Manager, Process
from traceback import print_exc
import uuid

class Swim(Base):
    def __init__(self, opts):
        self.status = SwimStatus.STOPPED
        self.opts = SwimOptions(opts)
        self.membership = Membership(opts)
        self.failure_check = FailureCheck(opts)
        self.manager = Manager()
    def start(self):
        membership_processes = []
        def run_failure_process(main_queue, failure_queue):
           logger.info("STARTING FAILURE HANDLING THREAD")
           self.failure_check.queue = main_queue
           self.failure_check.recv_queue = failure_queue
           self.failure_check.start()
        def run_server_process(main_queue, server_queue):
           logger.info("STARTING SWIM MESSAGE HANDLING THREAD")
           logger.info("STARTING SWIM ON %s"%(self.opts.local,))
           splitted = self.opts.local.split(":")
           server = SwimServer((splitted[0], int(splitted[1]),), SwimServerHandler, self.opts)
           server.queue = main_queue
           server.recv_queue = server_queue
           server.serve_forever()
        def run_membership_process(main_queue, membership_queue, member, membership):
           logger.info("STARTING MEMBERSHIP UPDATE PROCESS")
           membership.queue = main_queue
           membership.recv_queue = membership_queue
           membership.update(member)
        def find_membership_process(pid):
            for process in membership_processes:
                if process.pid == pid:
                    return process

        main_queue = self.manager.Queue()
        failure_queue = self.manager.Queue()
        server_queue = self.manager.Queue()
        process1 = Process(target=run_failure_process, args=(main_queue,failure_queue,))
        process1.daemon = True
        process1.start()
        process2 = Process(target=run_server_process, args=(main_queue,server_queue,))
        process2.daemon = True
        process2.start()

        while True:
            try:
                message = main_queue.get()
                logger.info("RECEIVED MESSAGE: %s"%( message.type, ))
                if message.type == MessageProcTypes.UPDATE_MEMBER_START:
                      membership_queue = self.manager.Queue()
                      membership_process = MembershipProcess(target=run_membership_process,
                            args=(
                                main_queue,
                                membership_queue,
                                message.data,
                                self.membership),
                            queue=membership_queue)
                      membership_processes.append( membership_process )
                      membership_process.daemon = True
                      membership_process.start()
                if message.type == MessageProcTypes.UPDATE_MEMBER:
                     self.membership.update_member( message.data )
                elif message.type == MessageProcTypes.RELAY_MEMBERS:
                     relay_members = self.membership.fetch_relay_members()
                     failure_queue.put( relay_members )
                elif message.type == MessageProcTypes.NEXT_CANDIDATE:
                     candidate = self.membership.next_candidate()
                     failure_queue.put( candidate )
                elif message.type == MessageProcTypes.MEMBER:
                    ## find which membership queue requested this member
                    member = self.membership.from_host_and_port(message.data.member.get_host(), message.data.member.get_port())
                    response_process= find_membership_process(message.data.pid)
                    response_process.queue.put(member)
                    del response_queue
                elif message.type == MessageProcTypes.SYNC:
                     member = message.data
                     self.membership.members.append( member )
            except Exception, ex:
                print_exc( ex )
                pass
