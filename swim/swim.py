
from .failure_check import FailureCheck
from .membership import Membership
from .swim_exceptions import SwimException
from .swim_defaults import SwimDefaults
from .swim_server import SwimServer
from .swim_server_handler import SwimServerHandler
from .swim_status import SwimStatus
from .swim_options import SwimOptions
from .swim_dissemination_listen import SwimDisseminationListen
from .swim_dissemination_update import SwimDisseminationUpdate
from .swim_dissemination_process import SwimDisseminationProcess
from .transport_serializer import TransportSerializer
from .message import Message
from .message_types import MessageTypes
from .message_proc import MessageProc
from .message_proc_types import MessageProcTypes
from .message_proc_update import MessageProcUpdate
from .message_proc_disseminate import MessageProcDisseminate
from .member_local import MemberLocal
from . import logger, destination_to_host_port

from multiprocessing import Manager, Process
from traceback import print_exc
import uuid

class Swim(object):
    def __init__(self, opts):
        self.status = SwimStatus.STOPPED
        self.opts = SwimOptions(opts)

        host, port = destination_to_host_port(self.opts.local)
        self.membership = Membership(
            MemberLocal(host,port), opts)
        self.failure_check = FailureCheck(self.opts)
        self.update_queue = []
        self.dissemination_listen = SwimDisseminationListen(self.opts)
        self.manager = Manager()
    def start(self):
        dissemination_processes = []
        logger.info("STARTING SWIM WITH LOCAL %s"%(self.opts.local,))
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
           
        def run_dissemination_listen_process(main_queue, dissemination_queue):
           logger.info("STARTING DISSEMINATION LISTEN PROCESS")
           self.dissemination_listen.queue = main_queue
           self.dissemination_listen.recv_queue = dissemination_queue
           self.dissemination_listen.start()

        def run_dissemination_process(main_queue,  recv_queue, member, message):
             logger.info("STARTING DISSEMINATION UPDATE MEMBER PROCESS")
             update = SwimDisseminationUpdate(self.opts)
             update.queue = main_queue
             update.recv_queue = recv_queue
             update.update(member, message)

        def find_dissemination_process(pid):
            for process in dissemination_processes:
                if process.pid == pid:
                    return process
        def for_every_queue_member(connection_string, do_fn):
            for message in self.update_queue:
               if message.get_destination()==connection_string:
                    do_fn( message )
        def clear_queue(member):
            def remove(m):
                self.update_queue.remove(m)
            for_every_queue_member(member.connection_string(), remove)

        def find_dissemination_updates(member):
            update = []
            def append(m):
                update.append( m  )
            for_every_queue_member(member.connection_string(), append)
            return update
        def create_dissemination_process_if_needed(message):
              recv_queue = self.manager.Queue()
              state_message = message.message
              member =self.membership.from_host_and_port(
                    message.member.get_host(),
                    message.member.get_port())
              if not member:
                  return
              dissemination_process = SwimDisseminationProcess(target=run_dissemination_process,
                    args=(
                        main_queue,
                        recv_queue,
                        member,
                        state_message
                        ),
                    queue=recv_queue)
              self.update_queue.append( state_message )
              dissemination_processes.append( dissemination_process )
              dissemination_process.daemon = True
              dissemination_process.start()
              logger.info("DISSEMINATION UPDATE PROCESS STARTED ON PID %s"%( dissemination_process.pid, ))
        def do_remove_on_member_if_needed(member):
            member_memory = self.membership.from_host_and_port(
                        message.data.get_host(),
                        message.data.get_port())
            if not member_memory:
                return
            member_list = self.membership.get_members()
            member_list.remove( member_memory )


        main_queue = self.manager.Queue()
        failure_queue = self.manager.Queue()
        server_queue = self.manager.Queue()
        dissemination_listen_queue = self.manager.Queue()
        process1 = Process(target=run_failure_process, args=(main_queue,failure_queue,))
        process1.daemon = True
        process1.start()
        process2 = Process(target=run_server_process, args=(main_queue,server_queue,))
        process2.daemon = True
        process2.start()
        process3 = Process(target=run_dissemination_listen_process, args=(main_queue,dissemination_listen_queue,))
        process3.daemon = True
        process3.start()
        ## disseminate this node joining
        local_member = self.membership.get_member_local()
        main_queue.put(
          MessageProcDisseminate(local_member,Message(MessageTypes.JOIN, **dict(
                origin=local_member.connection_string(),
                destination=local_member.connection_string()
             )) )
         )


        while True:
            try:
                message = main_queue.get()
                logger.debug("RECEIVED MESSAGE: %s"%( message.type, ))
                if message.type == MessageProcTypes.RELAY_MEMBERS:
                     relay_members = self.membership.fetch_relay_members(message.data)
                     failure_queue.put( relay_members )
                elif message.type == MessageProcTypes.NEXT_CANDIDATE:
                     candidate = self.membership.next_candidate()
                     failure_queue.put( candidate )
                elif message.type == MessageProcTypes.MEMBER_LOCAL_FAILURE:
                    member_local = self.membership.get_member_local()
                    failure_queue.put(member_local)
                elif message.type == MessageProcTypes.MEMBER_LOCAL_DISSEMINATE:
                    member_local = self.membership.get_member_local()
                    dissemination_listen_queue.put(member_local)
                elif message.type == MessageProcTypes.MEMBER_LOCAL_SERVER:
                    member_local = self.membership.get_member_local()
                    server_queue.put(member_local)
                elif message.type == MessageProcTypes.MEMBER_LOCAL_INCREMENT:
                    member_local = self.membership.get_member_local()
                    member_local.increment_incarnation()
                elif message.type == MessageProcTypes.MEMBER_MESSAGE:
                    member_memory = self.membership.from_host_and_port(
                        message.member.get_host(),
                        message.member.get_port())
                    member_memory.append_message( message.message )
                elif message.type == MessageProcTypes.MEMBERS_DISSEMINATE:
                    members = self.membership.get_members() 
                    dissemination_listen_queue.put(members)
                elif message.type == MessageProcTypes.DISSEMINATE:
                    dissemination_message = MessageProcDisseminate(
                        message.member,
                        message.message,
                        self.membership.get_member_local(),
                        self.membership.get_members())
                    dissemination_listen_queue.put(dissemination_message)
                elif message.type == MessageProcTypes.FAULTY_MEMBER:
                    logger.info("REMOVING FAULTY MEMBER %s"%(message.data.connection_string(),))
                    do_remove_on_member_if_needed(message.data)
                elif message.type == MessageProcTypes.JOIN:
                    logger.info("ADDING NEW MEMBER %s IF NEEDED"%(message.data.connection_string(),))
                    self.membership.add_member_if_needed(message.data)
                elif message.type == MessageProcTypes.DISSEMINATION_UPDATE:
                      create_dissemination_process_if_needed(message)
                elif  message.type == MessageProcTypes.DISSEMINATION_CLEAR:
                     member = message.data.member
                     clear_queue(member)
                elif message.type == MessageProcTypes.DISSEMINATION_UPDATES:
                     logger.info("DISSEMINATION_UPDATES MESSAGE FROM PID %s"%(message.data.pid,))
                     process = find_dissemination_process(message.data.pid)
                     updates = find_dissemination_updates(message.data.member)
                     process.queue.put(updates)
                elif message.type == MessageProcTypes.DISSEMINATION_VALID:
                     logger.info("DISSEMINATION_VALID MESSAGE FROM PID %s"%(message.data.pid,))
                     process = find_dissemination_process(message.data.pid)
                     member = self.membership.from_host_and_port(
                        message.data.member.get_host(),
                        message.data.member.get_port())
                     process.queue.put(member)
                elif message.type == MessageProcTypes.SERVER_MEMBER_EXISTS:
                     member = self.membership.from_host_and_port(
                        message.data.get_host(),
                        message.data.get_port())
                     server_queue.put(member)

            except Exception, ex:
                print_exc( ex )
                pass
