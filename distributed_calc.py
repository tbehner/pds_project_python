#!/usr/bin/env python3
import threading        # for Threads
from optparse import OptionParser
import time
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import xmlrpc.client
from distributed_server import *
from utility_functions import *
from netifaces import AF_INET
import netifaces as ni
import random

parser = OptionParser()
parser.add_option(
    "-c",
    "--connect",
    dest="server_con",
    help="connect to server with the given ip address and port number",
    metavar="ADDRESS:PORT")
parser.add_option(
    "-p",
    "--port",
    dest="port",
    help="open port with given number",
    metavar="PORT",
    type="int",
    default=2222)
parser.add_option(
    "--token-ring",
    dest="token_ring",
    action="store_true",
    help="set algorithm to token ring",
    default=False)
(options, args) = parser.parse_args()

def print_own_ip_addresses(port):
    ip_list = ni.interfaces()
    print("----------------------------------------")
    print("Server is listening to:")
    print("ip_list: {}".format(ip_list))
    for ip in ip_list:
        if AF_INET in ni.ifaddresses(ip).keys():
            print(ni.ifaddresses(ip)[AF_INET][0]['addr'] + ":" + str(port))

    print("----------------------------------------")

def generate_calculations(server_func, calculations_queue):
    calculations = [ "ServerFunction.calculationSum", "ServerFunction.calculationSubtract", "ServerFunction.calculationMultiply", "ServerFunction.calculationDivide", "ServerFunction.calculationStart" ]
#    rnd_time_lower_bound = 0.05
#    rnd_time_upper_bound = 0.5
    rnd_time_lower_bound = 0.5
    rnd_time_upper_bound = 1
    total_running_time = 20
    min_wait_time = 0.001
    start_time = time.time()
    current_time = time.time()

    # calculate next instance in time, that a calculation should be added
    next_calc_time = random.uniform(rnd_time_lower_bound, rnd_time_upper_bound) + time.time()
    while current_time - start_time < 20 or len(calculations_queue)>0:
        time.sleep(min_wait_time)
        if server_func.got_token and len(calculations_queue) > 0:
            next_op = calculations_queue.pop(0)
            print("Next operation to calculate: {}".format(next_op))
            if re.search("Start",next_op[0]):
                server_func.calculationStart(next_op[1][0])
            elif re.search("Sum",next_op[0]):
                server_func.calculationSum(next_op[1][0])
            elif re.search("Subtract",next_op[0]):
                server_func.calculationSubtract(next_op[1][0])
            elif re.search("Multiply",next_op[0]):
                server_func.calculationMultiply(next_op[1][0])
            elif re.search("Divide",next_op[0]):
                server_func.calculationDivide(next_op[1][0])

            print("Local restult: {}".format(server_func.calculated_value))

            for server in server_func.known_server_addr:
                con = xmlrcp.client.ServerProxy(get_con_string(server))
                getattr(con,next_op[0])(*next_op[1])

        if time.time() >= next_calc_time and current_time - start_time < 20:
            calculation_op    = calculations[random.randint(0,len(calculations)-2)]
            calculation_value = random.randint(1, 10)
            calculations_queue.append((calculation_op, [calculation_value]))

            next_calc_time    = random.uniform(rnd_time_lower_bound, rnd_time_upper_bound) + time.time()
        current_time = time.time()


def start_token_ring(server_func):
    while True:
        if len(server_func.known_server_addr) > 0:
            print("Got servers, need token...")
            if server_func.got_token:
                print("Got token from: {}".format(server_func.got_token_from))
                time.sleep(5)
                next_server, position = get_next_server(server_func)
                if next_server is None:
                    # i.e. wait for new servers
                    continue
                print("Next server {}".format(next_server))
                print("Do important calculations!")
                # pass token to next server
                print("Pass on token")
                try:
                    con = xmlrpc.client.ServerProxy(
                        get_con_string(next_server))
                    con.ServerFunctions.acceptToken(str(options.port))
                except:
                    print("ERROR:\nTrying again in a sec")
                    time.sleep(1)
                    continue
                # give up token when sure someone else got it
                server_func.got_token = False
        time.sleep(1)

def connect_to_server(connection, server_func):
    connection = translate_localhost(connection)
    print("Connecting to other server...")
    con = xmlrpc.client.ServerProxy(get_con_string(connection))
    con.ServerFunctions.registerRemoteServer(str(options.port))
    #server_func.known_server_addr.append(connection)
    print("...connected.")

"""
start server thread
"""
server = SimpleXMLRPCServer(("", options.port), ChattyRequestHandler)
# reset port, in case the port was arbitrary set by system
options.port = server.socket.getsockname()[1]
server_func = ServerFunctions(options.port)
server.register_instance(server_func)
server_thread = threading.Thread(target=start_serving, args=(server,))
server_thread.daemon = True
server_thread.start()

print_own_ip_addresses(options.port)

if options.server_con is not None:
    # connect to existing network
    connect_to_server(options.server_con, server_func)
    print("Initial server list: {}".format(server_func.known_server_addr))

if options.token_ring:
    # if the list of known_servers is empty get yourself a nice token
    if not options.server_con:
        server_func.got_token = True
    token_ring_thread = threading.Thread(
        target=start_token_ring,
        args=(
            server_func,
        ))
    token_ring_thread.daemon = True
    token_ring_thread.start()

print("Starting up program")
print("----------------------------------------")
print("Commands:")
print("\"stop\" to shut down the server and stop the program")
print("\"connect x.x.x.x:y\" to connect to server on ip x.x.x.x and port y")
print("\"start\" start the distributed calculation")
print("----------------------------------------")

ip4_addr_re = re.compile('(:?\d{1,4}\.){3}\d{1,4}')

try:
    while True:
        user_input = input('> ')

        if re.match('\s*stop', user_input):
            raise KeyboardInterrupt()

        if re.search('connect', user_input):
            mo = re.search('([.\w]+):(\d+)', user_input)
            # match for 'localhost' or an ip4 address
            if ip4_addr_re.search( mo.group(1)) or re.match( 'localhost', mo.group(1)):
                connect_to_server(mo.group(0), server_func)

        if re.match('\s*start',user_input):
            initial_value = float(random.randint(1,10))
            calc_queue = [('ServerFunction.calculationStart',[initial_value])]
            calc_thread = threading.Thread(target=generate_calculations,args=(server_func,calc_queue))
            calc_thread.daemon = True
            calc_thread.start()

# wait until shutdown
    server_thread.join()
except KeyboardInterrupt:
    print("Shutting down...")
    while server_func.got_token:
        time.sleep(5)

    print(
        "Unregister in complete list {}".format(
            server_func.known_server_addr))
    for s in server_func.known_server_addr:
        print("Unregister at server {}".format(s))
        con = xmlrpc.client.ServerProxy(get_con_string(s))
        con.ServerFunctions.unregisterRemoteServer(options.port)
