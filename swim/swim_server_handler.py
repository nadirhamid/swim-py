import SocketServer
import thread
import time
from multiprocessing import Queue
from . import logger, make_connection_string, destination_to_host_port
from .message_types import MessageTypes
from .message_proc import MessageProc
from .message_proc_types import MessageProcTypes
from .message_proc_update import MessageProcUpdate
from .message_proc_disseminate import MessageProcDisseminate
from .message import Message
from .member import Member
from .member_local import MemberLocal
from .swim_defaults import SwimDefaults
from .swim_client import SwimClient
from .swim_server import SwimServer
from .failure_check import FailureCheck
from traceback import print_exc


class SwimServerHandler(SwimClient, SocketServer.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.opts = server.opts
        self.queue = server.queue
        host, port = destination_to_host_port(self.opts.local) 
        self.local_member = MemberLocal(host, port)
        self.recv_queue = server.recv_queue
        self.handlers = {}
        self.handlers[MessageTypes.PING]=self.handle_ping
        self.handlers[MessageTypes.PING_REQUEST]=self.handle_ping_request
        self.handlers[MessageTypes.UPDATE]=self.handle_update
        self.handlers[MessageTypes.JOIN]=self.handle_join
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)

    def handle_ping(self, sender, message):
        logger.info("HANDLING PING")
        self.send_with_socket(sender, Message(MessageTypes.ACK))
    def handle_ping_request(self, sender, message):
        logger.info("HANDLING PING REQUEST")
        hostname = sender.getpeername()
        candidate = Member( message.get_destination_host(), message.get_destination_port() )
        failure_check = FailureCheck(self.opts)
        failure_check.routine_ping_request(
             sender, 
             candidate)
    def handle_update(self, sender, message):
        logger.info("HANDLING UPDATE")
        member = Member(message.get_destination_host(), message.get_destination_port())

        logger.info("HANDLING DISSEMINATION FOR HOST %s"%( member.connection_string() ))
        def do_update():
            self.queue.put(MessageProcUpdate(member, message))
        def handle_local_disseminate():
            if message.get_state()==MemberStatus.FAULTY:
                self.queue.put(MessageProc(MessageProcTypes.MEMBER_LOCAL_INCREMENT))
                alive_update = Message(MessageTypes.DISSEMINATION_UPDATE, **dict(
                    origin=self.local_member.connection_string(),
                    destination=self.local_member.connection_string(),
                   state=MemberStatus.ALIVE ))
                self.queue.put(MessageProcDisseminate(local_member, alive_update))
            do_update()
        def handle_disseminate():
            do_update()
            
        if ( message.get_destination()==self.local_member.connection_string() ):
           handle_local_disseminate()
        else:
           handle_disseminate()
        
    def handle_join(self, sender, message):
        logger.info("HANDLING JOIN")
        local_member = self.local_member
        new_member = Member(message.get_destination_host(), message.get_destination_port())
        if new_member.connection_string()==local_member.connection_string():
           return
        self.queue.put(MessageProc(MessageProcTypes.SERVER_MEMBER_EXISTS, new_member))
        member = self.recv_queue.get()
        if member:
           return 

        self.queue.put(MessageProc(MessageProcTypes.JOIN,new_member))
        self.queue.put(
          MessageProcDisseminate(new_member,Message(MessageTypes.JOIN, **dict(
                origin=self.local_member.connection_string(),
                destination=new_member.connection_string()
             )) )
         )
    def handle(self):
        try:
            data = self.request.recv(SwimDefaults.BUFFER_SIZE)
            logger.info("RECEIVED A MESSAGE %s"%( data, ))
            packet = self.opts.transport_serializer.loads( data )
            message = Message.from_dict(packet)
            logger.info("RECEIVED A MESSAGE TYPE %s"%( message.get_type(), ))
            self.handlers[ packet['type'] ] ( self.request, message )
        except Exception,ex:
            print_exc(ex)
            hostname =self.request.getpeername()
            logger.info("HANDLER FAILED FOR %s"%(hostname,))
            logger.info("PARSE MESSAGE FAILED FOR SENDER %s, DATA %s"%( make_connection_string( hostname[0], hostname[1] ), data ))
        self.request.close()
