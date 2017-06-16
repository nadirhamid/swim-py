
from multiprocessing import Process

class MembershipProcess(Process):
    def __init__(self, target=None, args=None, queue=None):
         Process.__init__(self, target=target, args=args)
         self.queue = queue
