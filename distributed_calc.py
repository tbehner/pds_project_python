#!/usr/bin/env python3
import threading        # for Threads
from optparse import OptionParser
import time
from xmlrpc.server  import SimpleXMLRPCServer
from xmlrpc.server  import SimpleXMLRPCRequestHandler
import xmlrpc.client
from distributed_server import *
from utility_functions import *
from netifaces import AF_INET, AF_INET6, AF_LINK, AF_PACKET, AF_BRIDGE
import netifaces as ni

parser = OptionParser()
parser.add_option("-c", "--connect", dest="server_con", help="connect to server with the given ip address and port number", metavar="ADDRESS:PORT")
parser.add_option("-p", "--port", dest="port", help="open port with given number", metavar="PORT", type="int", default=0)
(options,args) = parser.parse_args()

def print_own_ip_addresses(port):
    ip_list = ni.interfaces()
    print("----------------------------------------")
    print("Server is listening to:")
    for ip in ip_list:
        print(ni.ifaddresses(ip)[AF_INET][0]['addr'] + ":" + str(port))
    print("----------------------------------------")

def start_token_ring(server_func):
    while True:
        if len(server_func.known_server_addr)>0:
            print("HEY! Es ist mindestens ein Server bekannt")
            if server_func.got_token:
                server_func.got_token = False
                print("Got token from: {}".format(server_func.got_token_from))
                next_server = get_next_server(server_func)
                print("Next server {}".format(next_server))
                time.sleep(2)
                # FIXME do some important calculations
                print("Do important calculations!")
                # pass token to next server
                print("Pass on token")
                print("Server " + next_server)
                print("Server " + get_con_string(next_server))
                con = xmlrpc.client.ServerProxy(get_con_string(next_server))
                con.ServerFunctions.acceptToken(str(options.port))
        time.sleep(1)

"""
start server thread
"""
server = SimpleXMLRPCServer(("",options.port),ChattyRequestHandler)
# reset port, in case the port was arbitrary set by system
options.port = server.socket.getsockname()[1]
server_func = ServerFunctions(options.port)
server.register_function(server_func.registerRemoteServer, 'ServerFunctions.registerRemoteServer')
server.register_function(server_func.unregisterRemoteServer, 'ServerFunctions.unregisterRemoteServer')
server.register_function(server_func.refreshRemoteServerList, 'ServerFunctions.refreshRemoteServerList')
server.register_function(server_func.acceptToken, 'ServerFunctions.acceptToken')
#server.register_instance(server_func, True)
server_thread = threading.Thread(target=start_serving,args=(server,))
server_thread.daemon = True
server_thread.start()

print_own_ip_addresses(options.port)

if options.server_con is not None:
#connect to existing network
    options.server_con = translate_localhost(options.server_con)
    print("Connecting to other server...")
    con = xmlrpc.client.ServerProxy(get_con_string(options.server_con))
    con.ServerFunctions.registerRemoteServer(str(options.port))
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
        con.ServerFunctions.unregisterRemoteServer(options.port)
