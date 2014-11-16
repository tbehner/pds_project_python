#!/usr/bin/env python3
import threading        # for Threads
import sys              # maybe I don't need this, let's see
import socket           # for sockets 
import re               # regular expressions
from optparse import OptionParser

class Server:
    def __init__(self,ip,port):
        self.ip = ip
        self.port = port


parser = OptionParser()
parser.add_option("-c", "--connect", dest="server_con", help="connect to server with the given ip address and port number", metavar="ADDRESS:PORT")
parser.add_option("-p", "--port", dest="port", help="open port with given number", metavar="PORT", type="int", default=2222)
parser.add_option("--client", action="store_true", dest="is_client", default=False, help="act as a client")
parser.add_option("--server", action="store_true", dest="is_server", default=False, help="act as a server")

(options,args) = parser.parse_args()

servers = []

if options.is_client:
    # Connect to another server if such was stated on the command line
    if not options.server_con is None:
        ip_port_re = re.compile(r"([^:]+):([^:]+)")
        m = ip_port_re.match(options.server_con)
        server_ip_address = m.group(1)
        server_port       = m.group(2)
        servers.append(Server(server_ip_address,int(server_port)))

        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((server_ip_address,int(server_port)))


if options.is_server:
    # start own server
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((socket.gethostname(),options.port))
    serversocket.listen(5)

    clients = []
    try:
        while True:
            clientsocket, address = serversocket.accept()
            print("New clientsocket: {} with address: {}".format(clientsocket,address))
            clients.append((clientsocket,address))
    except(KeyboardInterrupt,SystemExit):
        print("Shutting down...")
        for (socket,addr) in clients:
            socket.close()
        serversocket.close()
        if not clientsocket is None:
            clientsocket.close()

    print("... and offline!")

