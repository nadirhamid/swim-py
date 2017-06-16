import SocketServer
import thread
import time
from multiprocessing import Queue
from . import logger, make_connection_string
from .message_types import MessageTypes
from .message_proc import MessageProc
from .message_proc_types import MessageProcTypes
from .message import Message
from .member import Member
from .swim_defaults import SwimDefaults
from .swim_client import SwimClient
from .swim_server import SwimServer
from .failure_check import FailureCheck
from traceback import print_exc


class SwimServerHandler(SwimClient, SocketServer.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.opts = server.opts
        self.handlers = {}
        self.handlers[MessageTypes.PING]=self.handle_ping
        self.handlers[MessageTypes.PING_REQUEST]=self.handle_ping_request
        self.handlers[MessageTypes.UPDATE]=self.handle_update
        self.handlers[MessageTypes.SYNC]=self.handle_sync
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
        def handle_local_disseminate():
            if message.get_state()==MemberStatus.FAULTY:
                self.queue.put(MessageProc(MessageProcTypes.MEMBER_LOCAL_INCREMENT))
                alive_update = Message(MessageTypes.UPDATE, **dict(
                    destination=local_member.connection_string(),
                   state=MemberStatus.ALIVE ))
                self.queue.put(MessageProc(MessageProcTypes.DISSEMINATE, alive_update))
        def handle_disseminate():
            self.queue.put(MessageProcDisseminate(message, member))
            
        if ( message.connection_string()==local_member.connection_string() ):
           handle_local_disseminate()
        else:
           handle_dissemninate()
        
    def handle_sync(self, sender, message):
        member = Member(message.get_host(), message.get_port())
        self.queue.put(MessageProc(MessageProcTypes.SYNC,member))
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
