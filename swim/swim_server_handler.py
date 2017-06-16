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
        hostname = sender.getpeername()
        member = Member(hostname[0], hostname[1])
        self.do_request(member, Message(MessageTypes.ACK))
    def handle_ping_request(self, sender, message):
        hostname = sender.getpeername()
        candidate = Member( message.get_host(), message.get_port() )
        origin = Member(hostname[0], hostname[1])

        failure_check = FailureCheck(self.opts)
        failure_check.routine_ping_request(
             origin, 
             candidate)
    def handle_update(self, sender, message):
        self.server.swim.membership.update(message)
    def handle_sync(self, sender, message):
        member = Member(message.get_host(), message.get_port())
        self.queue.put(MessageProc(MessageProcTypes.SYNC,member))
    def handle(self):
        try:
            data = self.request.recv(SwimDefaults.BUFFER_SIZE)
            packet = self.opts.transport_serializer.loads( data )
            message = Message.from_dict(packet)
            logger.info("RECEIVED A MESSAGE TYPE %s"%( message.get_type(), ))
            self.handlers[ packet['type'] ] ( self.request, message )
        except Exception,ex:
            print_exc(ex)
            hostname =self.request.getpeername()
            logger.info("HANDLER FAILED FOR %s"%(hostname,))
            logger.info("PARSE MESSAGE FAILED FOR SENDER %s, DATA %s"%( make_connection_string( hostname[0], hostname[1] ), data ))
