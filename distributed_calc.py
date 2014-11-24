#!/usr/bin/env python3
import threading        # for Threads
import sys              # maybe I don't need this, let's see
import re               # regular expressions
from optparse import OptionParser
import time
from xmlrpc.server  import SimpleXMLRPCServer
import xmlrpc.client

parser = OptionParser()
parser.add_option("-c", "--connect", dest="server_con", help="connect to server with the given ip address and port number", metavar="ADDRESS:PORT")
parser.add_option("-p", "--port", dest="port", help="open port with given number", metavar="PORT", type="int", default=2222)
parser.add_option("--client", action="store_true", dest="is_client", default=False, help="act as a client")
parser.add_option("--server", action="store_true", dest="is_server", default=False, help="act as a server")
(options,args) = parser.parse_args()


# List of all known server
servers = []

def register_new_server(ip_address,port):
    print("Added server {}:{} to the list of servers".format(ip_address,port))
    servers.append({'address': ip_address, 'port' : port})
    print(servers)
    for server in servers:
        # TODO hier einzelne Threads starten?
        if server['port'] == options.port:
            continue
        print("Next Server to populate list {}:{}".format(server['address'],server['port']))
        con_str = "http://{}:{}/".format(server['address'],server['port'])
        print("Server Adress: {}".format(con_str))
        con = xmlrpc.client.ServerProxy(con_str)
        con.check_server_list(servers)
    return 1

def check_server_list(server_list):
    for server in server_list:
        if not server in servers:
            servers.append(server)
            print("Added server {}:{} to the list of servers".format(server['address'],server['port']))
    return 1

def start_serving(server):
    try:
        print("Server started...")
        server.serve_forever()
        # send information about all known servers to the new one
        # send the information of the new server to all other known servers
    except:
        print("Not foreseen shutdown")
    print("... and offline!")


# start own server
server = SimpleXMLRPCServer(('localhost',options.port))
server.register_function(register_new_server,"register_new_server")
server.register_function(check_server_list,"check_server_list")
server_thread = threading.Thread(target=start_serving,args=(server,))
server_thread.daemon = True
server_thread.start()

servers.append({'address':'localhost','port':options.port})
print("thread should be started")

ip_port_re = re.compile(r"([^:]+):([^:]+)")

# Connect to another server if such was stated on the command line
if not options.server_con is None:
    m = ip_port_re.match(options.server_con)
    server_ip_address = m.group(1)
    server_port       = m.group(2)

    servers.append({'address' : server_ip_address, 'port' : int(server_port)})
    print("Connected to other server...")
    con = xmlrpc.client.ServerProxy("http://" + options.server_con + "/")
    con.register_new_server('localhost',options.port)
    print("Message send...")
else:
    servers.append({'address':'localhost','port':options.port})

try:
    server_thread.join()
except KeyboardInterrupt:
    print("Shutting down...")
