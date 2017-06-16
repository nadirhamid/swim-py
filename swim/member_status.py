
class MemberStatus(object):
    FAULTY = 0
    SUSPECT = 1
    ALIVE = 2
    def get_status(self):
       return self.status
    def set_status(self, status):
       self.status = status
