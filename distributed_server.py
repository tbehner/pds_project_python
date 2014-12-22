import threading        # for Threads
import sys              # maybe I don't need this, let's see
import re               # regular expressions
from optparse import OptionParser
import time
from xmlrpc.server  import SimpleXMLRPCServer
from xmlrpc.server  import SimpleXMLRPCRequestHandler
import xmlrpc.client
from utility_functions import *

class ChattyRequestHandler(SimpleXMLRPCRequestHandler):
    log = []
    def __init__(self, request, client_address, server):
        # Ich weiß noch nicht an welcher Stelle ich das hier überhaupt abrufen kann
        ChattyRequestHandler.log.append(client_address)
        SimpleXMLRPCRequestHandler.__init__(self, request, client_address, server)

class ServerFunctions:
    def __init__(self):
        self.known_server_addr = []

    def __populate_servers():
        # FIXME hier ist irgendwo ein Bug
        for server in self.known_server_addr:
            # all addresses are populated, except the address of the server the list gets populated to
            populated_servers = self.known_server_addr.copy()
            populated_servers.remove(server)
            con = xmlrpc.client.ServerProxy(get_con_string(server))
            con.check_server_list(populated_servers)

# 
# methods to be served
#
    def remove_server(self,client_port):
        server = get_addr_string(ChattyRequestHandler.log[-1][0],client_port)
        print("Saying bye to server {}".format(server))
        self.known_server_addr.remove(server)
        #populate_servers()
        return 0

    def register_new_server(self,client_port):
        # FIXME das muss vielleicht angepasst werden (formattierung nicht klar)
        server_addr = get_addr_string(ChattyRequestHandler.log[-1][0],client_port)
        print("Incomming connection: {}".format(server_addr))
        print("Known servers: {}".format(self.known_server_addr))
        if server_addr not in self.known_server_addr:
            print("New server {}".format(server_addr))
            self.known_server_addr.append(server_addr)
            #populate_servers()
        return 1

    def check_server_list(self,server_list):
        self.known_server_addr = server_list
        #print(servers)
        return 1


