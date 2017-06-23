
from .swim_client import SwimClient
from .swim_exceptions import SwimDisseminationFailedException
from .swim_dissemination_update import SwimDisseminationUpdate
from .swim_dissemination_process import SwimDisseminationThread
from .message_proc import MessageProc
from .message_proc_types import MessageProcTypes
from . import logger
from multiprocessing import Manager
from traceback import print_exc

class SwimDisseminationQueue(object):
    def __init__(self, opts):
       self.opts = opts
       ## tuple of updates as Member, MemberMessage
       self.update_queue = []
       self.manager = Manager()
    def start(self):
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
             
        while True:
           try:
              message =self.recv_queue.get()
              logger.info("DISSEMINATION QUEUE RECEIVED WORK OF TYPE %s"%( message.type ) )
              if message.type == MessageProcTypes.DISSEMINATION_UPDATE:
                      d_queue = self.manager.Queue()
                      recv_queue = self.manager.Queue()
                      state_message = message.message
                      member = message.member
                      dissemination_process = SwimDisseminationThread(target=run_dissemination_process,
                            args=(
                                self.queue,
                                d_queue,
                                recv_queue,
                                member,
                                state_message
                                ),
                            recv_queue=recv_queue,
                            d_queue=d_queue)
                      self.update_queue.append( state_message )
                      dissemination_processs.append( dissemination_process )
                      dissemination_process.daemon = True
                      dissemination_process.start()

              elif  message.type == MessageProcTypes.DISSEMINATION_CLEAR:
                 member = message.data.member
                 clear_queue(member)
              elif message.type == MessageProcTypes.DISSEMINATION_UPDATES:
                 process = find_dissemination_process(message.data.pid)
                 updates = find_dissemination_updates(message.data.member)
                 process.recv_queue.put(updates)
           except Exception,ex:
              print_exc(ex)
        
            
