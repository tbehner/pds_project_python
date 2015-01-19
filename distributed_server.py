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
        ChattyRequestHandler.log.append(client_address)
        SimpleXMLRPCRequestHandler.__init__(self, request, client_address, server)

class ServerFunctions:
    def __init__(self, own_port):
        self.known_server_addr = []
        self.got_token = False
        self.got_token_from = None
        self.next_token_server = None
        self.lock = threading.Lock()
        self.own_port = own_port
        self.calculated_value = None

    def _dispatch(self, method, params):
        method_name = str(method)
        method_name_parts = method_name.split(".")
        method_name = method_name_parts[-1]
        func_output = getattr(ServerFunctions, method_name)(self, *params)
        return func_output
        
    def __populate_servers(self):
        for server in self.known_server_addr:
            print("Populate server list to {}".format(server))
            # all addresses are populated, except the address of the server the list gets populated to
            populated_servers = self.known_server_addr.copy()
            populated_servers.remove(server)
            # by convention: first entry is own port without ip
            populated_servers.insert(0, str(self.own_port))
            con = xmlrpc.client.ServerProxy(get_con_string(server))
            con.ServerFunctions.refreshRemoteServerList(populated_servers)

# 
# methods to be served
#
    def unregisterRemoteServer(self,client_port):
        server = get_addr_string(ChattyRequestHandler.log[-1][0],client_port)
        if server in self.known_server_addr:
            print("Saying bye to server {}".format(server))
            self.known_server_addr.remove(server)
        else:
            print("Bye from unknown server{}".format(server))
        print("Updated server list {}".format(self.known_server_addr))
        return 1

    def registerRemoteServer(self,client_port):
        server_addr = get_addr_string(ChattyRequestHandler.log[-1][0],client_port)
        print("Register new server {}".format(server_addr))
        if server_addr not in self.known_server_addr:
            self.known_server_addr.append(server_addr)
        self.__populate_servers()
        print("New Server list: {}".format(self.known_server_addr))
        return 1

    def refreshRemoteServerList(self,server_list):
        print("Get new server list {}".format(server_list))
        for i in range(len(server_list)):
            if i==0:
                server = get_addr_string(ChattyRequestHandler.log[-1][0], server_list[i])
            else:
                server = server_list[i]
            if server not in self.known_server_addr:
                self.known_server_addr.append(server)
        print("New Server list: {}".format(self.known_server_addr))
        return 1

    def acceptToken(self,client_port):
        print("I got the token!")
        self.got_token = True
        self.got_token_from = get_addr_string(ChattyRequestHandler.log[-1][0],client_port)
        return 1

    def calculationStart(self,value):
        self.calculation_value = value

    def calculationSum(self,value):
        self.calculation_value+=value

    def calculationSubtract(self,value):
        self.calculation_value-= value

    def calculationMultiply(self,value):
        self.calculation_value*= value

    def calculationDivide(self,value):
        self.calculation_value/= value


