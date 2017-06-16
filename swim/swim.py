
from .failure_check import FailureCheck
from .membership import Membership
from .swim_exceptions import SwimException
from .swim_defaults import SwimDefaults
from .swim_server import SwimServer
from .swim_server_handler import SwimServerHandler
from .swim_status import SwimStatus
from .swim_options import SwimOptions
from .swim_dissemination_listen import SwimDisseminationListen
from .swim_dissemination_queue import SwimDisseminationQueue
from .swim_dissemination_update import SwimDisseminationUpdate
from .transport_serializer import TransportSerializer
from .message import Message
from .message_type import MessageType
from .message_proc import MessageProc
from .message_proc_types import MessageProcTypes
from .dissemination_process import SwimDisseminationProcess
from .member_local import MemberLocal
from . import logger
from multiprocessing import Manager, Process
from traceback import print_exc
import uuid

class Swim(object):
    def __init__(self, opts):
        self.status = SwimStatus.STOPPED
        self.opts = SwimOptions(opts)
        self.membership = Membership(
            MemberLocal(self.opts.local), opts)
        self.failure_check = FailureCheck(opts)
        self.dissemnination_listen = SwimDisseminationListen(opts)
        self.dissemnination_update = SwimDisseminationUpdate(opts)
        self.manager = Manager()
    def start(self):
        dissemination_processes = []
        def run_failure_process(main_queue, recv_queue):
           logger.info("STARTING FAILURE HANDLING THREAD")
           self.failure_check.queue = main_queue
           self.failure_check.recv_queue = recv_queue
           self.failure_check.start()
        def run_server_process(main_queue, recv_queue):
           logger.info("STARTING SWIM MESSAGE HANDLING THREAD")
           logger.info("STARTING SWIM ON %s"%(self.opts.local,))
           splitted = self.opts.local.split(":")
           server = SwimServer((splitted[0], int(splitted[1]),), SwimServerHandler, self.opts)
           server.queue = main_queue
           server.recv_queue = recv_queue
           server.serve_forever()
        def run_dissemination_process(main_queue, dissemination_queue, member):
           logger.info("STARTING MEMBERSHIP UPDATE PROCESS")
           update = SwimDisseminationUpdate(self.opts.original)
           update.update_member(member)
           
        def run_dissemination_listen_process(main_queue, dissemination_queue):
           logger.info("STARTING DISSEMINATION LISTEN PROCESS")
           self.dissemniation.recv_queue = dissemination_queue
           self.dissemination.start()

        def run_dissemination_queue_process(main_queue, dissemination_queue):
           logger.info("STARTING DISSEMINATION QUEUE PROCESS")
           self.dissemniation_update_queue.recv_queue = dissemination_queue
           self.dissemination_update_queue.start()

        def run_sync_process(main_queue, membership):
            swim_client = SwimClient()
            swim_client.opts = self.opts
            members = membership.get_members()
            for member in members:
                swim_client.send(member,
            

        def find_dissemination_process(pid):
            for process in dissemination_processes:
                if process.pid == pid:
                    return process

        main_queue = self.manager.Queue()
        failure_queue = self.manager.Queue()
        server_queue = self.manager.Queue()
        dissemination_listen_queue = self.manager.Queue()
        dissemination_update_queue = self.manager.Queue()
        process1 = Process(target=run_failure_process, args=(main_queue,failure_queue,))
        process1.daemon = True
        process1.start()
        process2 = Process(target=run_server_process, args=(main_queue,server_queue,))
        process2.daemon = True
        process2.start()
        process3 = Process(target=run_dissemination_listen_process, args=(main_queue,dissmeination_listen_queue,))
        process3.daemon = True
        process3.start()
        process4 = Process(target=run_dissemination_queue_process, args=(main_queue,dissmeination_queue_queue,))
        process4.daemon = True
        process4.start()

        while True:
            try:
                message = main_queue.get()
                logger.info("RECEIVED MESSAGE: %s"%( message.type, ))
                if message.type == MessageProcTypes.DISSEMINATION_UPDATE:
                     dissemination_update_queue.put( message )
                if message.type == MessageProcTypes.UPDATE_MEMBER:
                     self.membership.update_member( message.data )
                elif message.type == MessageProcTypes.RELAY_MEMBERS:
                     relay_members = self.membership.fetch_relay_members(message.data)
                     failure_queue.put( relay_members )
                elif message.type == MessageProcTypes.NEXT_CANDIDATE:
                     candidate = self.membership.next_candidate()
                     failure_queue.put( candidate )
                elif message.type == MessageProcTypes.MEMBER:
                    ## find which membership queue requested this member
                    member = self.membership.from_host_and_port(message.data.member.get_host(), message.data.member.get_port())
                    response_process= find_dissemination_process(message.data.pid)
                    response_process.queue.put(member)
                    del response_queue
                elif message.type === MessageProcTypes.MEMBER_LOCAL_FAILURE:
                    member_local = self.membership.get_member_local()
                    failure_queue.put(member_local)
                elif message.type === MessageProcTypes.MEMBER_LOCAL_DISSEMINATE:
                    member_local = self.membership.get_member_local()
                    dissemination_queue.put(member_local)
                elif message.type === MessageProcTypes.MEMBER_LOCAL_INCREMENT:
                    member_local = self.membership.get_member_local()
                    member_local.increment_incarnation()
                elif message.type == MessageProcTypes.MEMBER_MESSAGE:
                    member_memory = self.membership.from_host_and_port(
                        message.member.get_host(),
                        message.member.get_port())
                    member_memory.append_message( message.message )
                elif message.type == MessageProcTypes.DISSEMINATE:
                    dissemination_queue.put(message.data)
                elif message.type == MessageProcTypes.FAULTY_MEMBER:
                    member_memory = self.membership.from_host_and_port(
                        message.member.get_host(),
                        message.member.get_port())
                    member_list = self.membership.get_members()
                    member_list.remove( member_memory )
            except Exception, ex:
                print_exc( ex )
                pass
