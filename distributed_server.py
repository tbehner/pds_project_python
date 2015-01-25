from xmlrpc.server import SimpleXMLRPCRequestHandler
import xmlrpc.client
from pip import req
from utility_functions import *
import ricart_agrawala

class ChattyRequestHandler(SimpleXMLRPCRequestHandler):
    log = []
    connection_blocked = False
    def __init__(self, request, client_address, server):
        while ChattyRequestHandler.connection_blocked:
            time.sleep(0.001)
        ChattyRequestHandler.connection_blocked = True
        ChattyRequestHandler.log.append(client_address)
        SimpleXMLRPCRequestHandler.__init__(self, request, client_address, server)

    def do_POST(self):
        while not ChattyRequestHandler.connection_blocked:
            time.sleep(0.001)
        # call do_POST of super class
        super(ChattyRequestHandler,self).do_POST()

class ServerFunctions:
    def __init__(self, own_adress, own_port, chatty_token=False):
        self.known_server_addr = []
        self.received_replies_servers = []
        # dict of known servers (key) and their calculation queue (value)
        self.sync_strategy = ricart_agrawala.RicartAgrawalaAlgorithm(self)
        self.known_servers_calc_queues = {}
        self.got_token         = False
        self.got_token_from    = None
        self.next_token_server = None
        self.own_port          = own_port
        self.own_adress        = own_adress
        self.calculated_value  = None
        self.calc_thread       = None
        self.calc_queue        = []
        self.keep_token        = False
        self.token_on_way_to_next_server = False
        self.total_computations = 0
        self.chatty_token       = chatty_token
        # logical clock timestamp, init value is 0, we will change it at the start of each calculation
        self.clock_timestamp = 0
        self.reply_to_server_queue = []
        self.request_sent = False
        self.id = "{}:{}".format(self.own_adress, self.own_port)



    def _dispatch(self, method, params):
        method_name = str(method)
        method_name_parts = method_name.split(".")
        method_name = method_name_parts[-1]
        func_output = getattr(ServerFunctions, method_name)(self, *params)
        if method_name.startswith("calc"):
            print("")
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
        ChattyRequestHandler.connection_blocked = False
        return 1

    def registerRemoteServer(self,client_port):
        server_addr = get_addr_string(ChattyRequestHandler.log[-1][0],client_port)
        print("Register new server {}".format(server_addr))
        if server_addr not in self.known_server_addr:
            self.known_server_addr.append(server_addr)
        self.__populate_servers()
        print("New Server list: {}".format(self.known_server_addr))
        ChattyRequestHandler.connection_blocked = False
        return 1

    def refreshRemoteServerList(self,server_list):
        for i in range(len(server_list)):
            if i==0:
                server = get_addr_string(ChattyRequestHandler.log[-1][0], server_list[i])
            else:
                server = server_list[i]
            if server not in self.known_server_addr:
                self.known_server_addr.append(server)
        ChattyRequestHandler.connection_blocked = False
        return 1

    def acceptToken(self,client_port):
        self.got_token = True
        self.got_token_from = get_addr_string(ChattyRequestHandler.log[-1][0],client_port)
        ChattyRequestHandler.connection_blocked = False
        if self.chatty_token:
            print("Got token from {}".format(self.got_token_from))
        return 1

    def list(self):
        for server_addr in self.known_server_addr:
            print(server_addr)

    def calculationStart(self,value,start_thread=True,timing='normal'):
        self.calculated_value = value
        if start_thread:
            calc_thread = threading.Thread(target=generate_calculations,args=(self,self.calc_queue,translate_timing_to_dict(timing),))
            calc_thread.daemon = True
            calc_thread.start()
            ChattyRequestHandler.connection_blocked = False
        return self.calculated_value

    def calculationSum(self,value):
        self.calculated_value = self.calculated_value + value
        print("+ {} = {}".format(value, self.calculated_value))
        self.total_computations = self.total_computations + 1
        ChattyRequestHandler.connection_blocked = False
        return self.calculated_value

    def calculationSubtract(self,value):
        self.calculated_value = self.calculated_value - value
        print("- {} = {}".format(value, self.calculated_value))
        self.total_computations = self.total_computations + 1
        ChattyRequestHandler.connection_blocked = False
        return self.calculated_value

    def calculationMultiply(self,value):
        self.calculated_value = self.calculated_value * value
        print("* {} = {}".format(value, self.calculated_value))
        self.total_computations = self.total_computations + 1
        ChattyRequestHandler.connection_blocked = False
        return self.calculated_value

    def calculationDivide(self,value):
        self.calculated_value = self.calculated_value / value
        print("/ {} = {}".format(value, self.calculated_value))
        self.total_computations = self.total_computations + 1
        ChattyRequestHandler.connection_blocked = False
        return self.calculated_value

    def requestAccess(self, request_site, request_clock):
        print("Received request from {}".format(request_site))
        # are we interested in the critical section and do we have higher priority?
        local_clock = self.clock_timestamp
        self._sync_clock(request_clock)
        if self.request_sent or (len(self.calc_queue) != 0 and local_clock < request_clock):
            # add server to reply list
            if request_site not in self.reply_to_server_queue:
                self.reply_to_server_queue.append(request_site)
                # otherwise send OK reply

        else:
            self.sendReply(request_site)
        ChattyRequestHandler.connection_blocked = False
        return 1

    def sendReply(self, request_site):
        con = xmlrpc.client.ServerProxy(get_con_string(request_site))
        print("Send OK reply to {}".format(request_site))
        self.clock_timestamp += 1
        con.replyOK(self.id, self.clock_timestamp)
        ChattyRequestHandler.connection_blocked = False
        return 1

    def replyOK(self, requesting_site, timestamp):
        print("Received OK from: {}".format(requesting_site))
        self.received_replies_servers.append(requesting_site)
        self.clock_timestamp += 1
        self._sync_clock(timestamp)
        ChattyRequestHandler.connection_blocked = False
        return 1

    def _sync_clock(self, received_clock_timestamp):
        print("Sync clocktime - own time: {} received: {} | ". format(self.clock_timestamp, received_clock_timestamp), end="")
        self.clock_timestamp = max(self.clock_timestamp, received_clock_timestamp)+1
        print("New clocktime: {}".format(self.clock_timestamp))


    def queueOperation(self, server, operation):
        if not server in self.known_servers_calc_queues:
            self.known_servers_calc_queues[server] = []
        self.known_servers_calc_queues[server].append(operation)
        ChattyRequestHandler.connection_blocked = False
        return 1

    def performOwnCalculations(self, index):
        print("Performing own operations...")
        self.clock_timestamp += 1
        self._performCalculations(index, self.calc_queue)
        ChattyRequestHandler.connection_blocked = False
        return 1

    def performRemoteCalculations(self, index, server):
        print("Perfoming remote operations of {}".format(server))
        self.clock_timestamp += 1
        if server in self.known_server_addr:
            self._performCalculations(index, self.known_servers_calc_queues[server])
        ChattyRequestHandler.connection_blocked = False
        return 1

    def _performCalculations(self, index, queue):
        # should not happen, but who knows
        if queue is None:
            print('the index is higher than the queue length, we are missig some operations, abort the calculation')
            return 1
        if not queue:
            # nothing to do queue is empty
            ChattyRequestHandler.connection_blocked = False
            return 1
        # sort and take the number of operation provided by index
        # it is possible that the server receives more operations inbetween
        # so we slice the ordered list
        sorted_queue = sorted(queue, key=lambda operation: operation[2])
        # this operation must be performed by the server
        operations_to_perform = sorted_queue[:index]
        # keep track of the counter, maybe we have lost some of the operations,
        # i.e we we have operations 1,2,4, we know that operation 3 is missing
        # so we have to abort the distributed calculation
        counter = operations_to_perform[0][2]
        for operation in operations_to_perform:
            # check the counter
            if operation[2] != counter:
                print('the counter does not match with the operation counter, we are missing some operations, abort the calculation')
                # wait to receiv the other operations
                return 1
            if re.search("Sum", operation[0]):
                self.calculationSum(value=operation[1][0])
            elif re.search("Subtract", operation[0]):
                self.calculationSubtract(value=operation[1][0])
            elif re.search("Multiply", operation[0]):
                self.calculationMultiply(value=operation[1][0])
            elif re.search("Divide", operation[0]):
                self.calculationDivide(value=operation[1][0])
            # increment counter
            counter += 1
        # removed the peformed operations
        if len(queue) >= len(operations_to_perform):
            del queue[:len(operations_to_perform)]

    def start(self, value, starter):
        print("Set start value to {}".format(value))
        self.calculated_value = value
        # if we've started the thread, notify other nodes
        if starter:
            self.clock_timestamp += 1
            for server in self.known_server_addr:
                con = xmlrpc.client.ServerProxy(get_con_string(server))
                print("Send start request to {}".format(server))
                con.start(value, False)
        else:
            self.sync_strategy.start(False)
        ChattyRequestHandler.connection_blocked = False
        return 1
