#!/usr/bin/env python3
import threading        # for Threads
import sys              # maybe I don't need this, let's see
import re               # regular expressions
from optparse import OptionParser
import time
from xmlrpc.server  import SimpleXMLRPCServer
import xmlrpc.client
import socket           # only needed for gethostname()

parser = OptionParser()
parser.add_option("-c", "--connect", dest="server_con", help="connect to server with the given ip address and port number", metavar="ADDRESS:PORT")
parser.add_option("-p", "--port", dest="port", help="open port with given number", metavar="PORT", type="int", default=2222)
parser.add_option("-a", "--address", dest="ip_address", help="own ip adress", metavar="ADDRESS", type="string", default='localhost')
parser.add_option("--client", action="store_true", dest="is_client", default=False, help="act as a client")
parser.add_option("--server", action="store_true", dest="is_server", default=False, help="act as a server")
(options,args) = parser.parse_args()

own_connection = 'localhost:{}'.format(options.port)

# List of all known servers in format 'address:port'
servers = []

"""
    local functions
    
    these are functions which are used by the programm working as a client
"""
# populate the server list to all known servers
def populate_servers():
    for server in servers:
        if server == own_connection:
            continue
        con = xmlrpc.client.ServerProxy(get_con_string(server))
        con.check_server_list(servers)

def start_serving(server):
    try:
        print("Server started...")
        server.serve_forever()
        # send information about all known servers to the new one
        # send the information of the new server to all other known servers
    except:
        print("Not foreseen shutdown")
    print("... and offline!")

def get_con_string(server):
    return "http://{}/".format(server)

"""
    server functions

    these are functions which are serverd by the xmlrpc server
"""

def remove_server(server):
    print("Saying bye to server {}".format(server))
    servers.remove(server)
    populate_servers()
    return 0

# it is assumed that server is given in the format 'address:port'
def register_new_server(server):
    if not server in servers:
        print("New server {}".format(server))
        servers.append(server)
        populate_servers()
    return 1

def check_server_list(server_list):
    servers = server_list
    print(servers)
    return 1

# start own server
server = SimpleXMLRPCServer(('localhost',options.port))
server.register_function(register_new_server,"register_new_server")
server.register_function(check_server_list,"check_server_list")
server.register_function(remove_server,"remove_server")
server_thread = threading.Thread(target=start_serving,args=(server,))
server_thread.daemon = True
server_thread.start()

servers.append(own_connection)
print("thread should be started")

# Connect to another server if such was stated on the command line
if not options.server_con is None:
    print("Connecting to other server...")
    con = xmlrpc.client.ServerProxy(get_con_string(options.server_con))
    con.register_new_server(own_connection)
    print("...connected.")
else:
    servers.append(own_connection)

try:
    server_thread.join()
except KeyboardInterrupt:
    if not options.server_con is None:
        con = xmlrpc.client.ServerProxy(get_con_string(options.server_con))
        con.remove_server(own_connection)
    else:
        for s in servers:
            if s != own_connection:
                con = xmlrpc.client.ServerProxy(get_con_string(s))
                con.remove_server(own_connection)
                break
    print("Shutting down...")

