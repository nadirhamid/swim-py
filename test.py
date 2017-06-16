from swim.swim import Swim
from swim.swim_server import SwimServer
from swim.swim_server_handler import SwimServerHandler
swim = Swim({"hosts": ["127.0.0.1:5901"]})
splitted = swim.opts.local.split(":")
server = SwimServer((splitted[0], int(splitted[1]),), SwimServerHandler, swim.opts)
server.serve_forever()

