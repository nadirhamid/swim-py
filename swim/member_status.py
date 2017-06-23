
class MemberStatus(object):
    FAULTY = "FAULTY"
    SUSPECT = "SUSPECT"
    ALIVE = "ALIVE"
    CONFIRM = "CONFIRM"
    def get_status(self):
       return self.status
    def set_status(self, status):
       self.status = status
