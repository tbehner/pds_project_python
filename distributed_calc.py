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


# List of all known server
servers = []

# gets called by register_new_server to populate the new server and all other known servers
def populate_servers():
    for server in servers:
    return 0

# gets called by other server to populate list of all known servers
def check_known_servers(server_list):
    return 0

def register_new_server(ip_address,port):
    print("Added server {}:{} to the list of servers".format(ip_address,port))
    servers.append({'address': ip_address, 'port' : port})
    print(servers)
    # populate_servers()
    return 1


# start own server
server = SimpleXMLRPCServer(('localhost',options.port))
server.register_function(register_new_server,"register_new_server")
print("Server started...")


# Connect to another server if such was stated on the command line
if not options.server_con is None:
    ip_port_re = re.compile(r"([^:]+):([^:]+)")
    m = ip_port_re.match(options.server_con)
    server_ip_address = m.group(1)
    server_port       = m.group(2)

    servers.append({'address' : server_ip_address, 'port' : int(server_port)})
    print("Connected to other server...")
    con = xmlrpc.client.ServerProxy("http://" + options.server_con + "/")
    con.register_new_server('localhost',options.port)
    print("Message send...")

try:
    server.serve_forever()
    # send information about all known servers to the new one
    # send the information of the new server to all other known servers
except(KeyboardInterrupt,SystemExit):
    print("Shutting down...")
except:
    print("Not foreseen shutdown")
print("... and offline!")

