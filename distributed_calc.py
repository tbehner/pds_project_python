#!/usr/bin/env python3
import threading        # for Threads
from optparse import OptionParser
import time
from xmlrpc.server  import SimpleXMLRPCServer
from xmlrpc.server  import SimpleXMLRPCRequestHandler
import xmlrpc.client
from distributed_server import *
from utility_functions import *

"""
TODOs:
    * Hier alles bereinigen, was sich über die Zeit angesammelt hat
    * mit Alexander kommunizieren wie wir die Algorithmen aufteilen
    * Algorithmus implementieren
"""

parser = OptionParser()
parser.add_option("-c", "--connect", dest="server_con", help="connect to server with the given ip address and port number", metavar="ADDRESS:PORT")
parser.add_option("-p", "--port", dest="port", help="open port with given number", metavar="PORT", type="int", default=2222)
(options,args) = parser.parse_args()

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
    print("Connecting to other server...")
    con = xmlrpc.client.ServerProxy(get_con_string(options.server_con))
    con.register_new_server(options.port)
    print("...connected.")

"""
wait until shutdown
"""
try:
    server_thread.join()
except KeyboardInterrupt:
    if not options.server_con is None:
        con = xmlrpc.client.ServerProxy(get_con_string(options.server_con))
        con.remove_server(options.port)
    else:
        for s in server_func.known_server_addr:
            con = xmlrpc.client.ServerProxy(get_con_string(s))
            con.remove_server(options.port)
            break
    print("Shutting down...")

