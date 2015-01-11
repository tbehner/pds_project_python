#!/usr/bin/env python3
import threading        # for Threads
from optparse import OptionParser
import time
from xmlrpc.server  import SimpleXMLRPCServer
from xmlrpc.server  import SimpleXMLRPCRequestHandler
import xmlrpc.client
from distributed_server import *
from utility_functions import *


parser = OptionParser()
parser.add_option("-c", "--connect", dest="server_con", help="connect to server with the given ip address and port number", metavar="ADDRESS:PORT")
parser.add_option("-p", "--port", dest="port", help="open port with given number", metavar="PORT", type="int", default=2222)
(options,args) = parser.parse_args()

def start_token_ring(server_func):
    while True:
        if len(server_func.known_server_addr)>0:
            print("HEY! Es ist mindestens ein Server bekannt")
            if server_func.got_token:
                server_func.got_token = False
                print("Got token from: {}".format(server_func.got_token_from))
                next_server = get_next_server(server_func)
                print("Next server {}".format(next_server))
                time.sleep(5)
                # FIXME do some important calculations
                print("Do important calculations!")
                # pass token to next server
                print("Pass on token")
                con = xmlrpc.client.ServerProxy(get_con_string(next_server))
                con.set_token(options.port)
        time.sleep(1)

"""
start server thread
"""
server = SimpleXMLRPCServer(("",options.port),ChattyRequestHandler)
server_func = ServerFunctions()
server.register_instance(server_func)
server_thread = threading.Thread(target=start_serving,args=(server,))
server_thread.daemon = True
server_thread.start()

if options.server_con is not None:
#connect to existing network
    options.server_con = translate_localhost(options.server_con)
    print("Connecting to other server...")
    con = xmlrpc.client.ServerProxy(get_con_string(options.server_con))
    con.registerRemoteServer(options.port)
    server_func.known_server_addr.append(options.server_con)
    print("...connected.")
    print("Initial server list: {}".format(server_func.known_server_addr))
else:
    server_func.got_token = True

token_ring_thread = threading.Thread(target=start_token_ring,args=(server_func,))
token_ring_thread.daemon = True
token_ring_thread.start()


"""
wait until shutdown
"""
try:
    server_thread.join()
except KeyboardInterrupt:
    print("Shutting down...")
    print("Unregister in complete list {}".format(server_func.known_server_addr))
    for s in server_func.known_server_addr:
        print("Unregister at server {}".format(s))
        con = xmlrpc.client.ServerProxy(get_con_string(s))
        con.unregisterRemoteServer(options.port)
