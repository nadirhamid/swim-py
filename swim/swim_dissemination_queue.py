
from .swim_client import SwimClient
from .swim_exceptions import SwimDisseminationFailedException
from .swim_dissemination_update import SwimDisseminationUpdate
from .swim_dissemination_process import SwimDisseminationProcess
from .mesage_proc import MessageProc
from .mesage_proc_types import MessageProcTypes
from . import logger
from multiprocessing import Manager

class SwimDisseminationQueue(object):
    def __init__(self, opts):
       self.opts = opts
       ## tuple of updates as Member, MemberMessage
       self.queue = []
       self.manager = Manager()
    def start(self):
        def run_dissemination_process(main_queue, recv_queue, member):
             update = SwimDisseminationUpdate(self.opts)
             update.recv_queue = recv_queue
             update.update_member(member)
        def find_dissemination_process(pid):
            for process in dissemination_processes:
                if process.pid == pid:
                    return process
        def clear_queue(message):
            for message in self.queue:
               if message[ 0 ].connection_string()==message.member.connection_string():
                  self.queue.remove( message )
        while True:
           try:
              message =self.recv_queue.get()
              if message.type == MessageProcTypes.DISSEMINATION_UPDATE:
                      dissemination_queue = self.manager.Queue()
                      dissemination_process = SwimDisseminationProcess(target=run_dissemination_process,
                            args=(
                                self.recv_queue,
                                dissemination_queue,
                                message.data,
                                self.membership),
                            queue=dissemination_queue)
                      dissemination_processes.append( dissemination_process )
                      dissemination_process.daemon = True
                      dissemination_process.start()

              elif  message.type == MessageProcTypes.DISSEMINATION_CLEAR:
                 clear_queue()
           except Exception,ex:
              print_exc(ex)
        
            
