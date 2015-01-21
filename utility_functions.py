from xmlrpc.server  import SimpleXMLRPCServer
import xmlrpc.client
import time
import re
import random

def translate_localhost(ip_string):
    ip_addr, port = re.split(':',ip_string)
    if re.match('localhost',ip_addr):
        return ':'.join(('127.0.0.1',port))
    else:
        return ip_string


def start_serving(server):
    try:
        print("Server started...")
        server.serve_forever()
        # send information about all known servers to the new one
        # send the information of the new server to all other known servers
    except:
        print("Not foreseen shutdown")
    print("... and offline!")

def get_addr_string(addr, port):
    return "{}:{}".format(addr,port)

def get_con_string(server):
    return "http://{}/".format(server)

# get next server in list
#<<<<<<< HEAD
def get_next_server(server_func,position=None):
    next_server = None
    next_server_idx = None

    # if there is no other known server return None
    if not server_func.known_server_addr:
        return next_server # which is None

    # if there is no previous server, get the first one
    if server_func.got_token_from is None:
        # start at first element
        return (server_func.known_server_addr[0],0)

    # if a position was given on the command line
    if position is not None:
        next_server_idx = position + 1
    else:
        next_server_idx = server_func.known_server_addr.index(server_func.got_token_from)+1

    # get next one
    if next_server_idx >= len(server_func.known_server_addr):
        # start over
        next_server_idx = 0
        next_server = server_func.known_server_addr[next_server_idx]

    return (next_server, next_server_idx)

def generate_calculations(server_func, calculations_queue):
    calculations = [ "ServerFunctions.calculationSum", "ServerFunctions.calculationSubtract", "ServerFunctions.calculationMultiply", "ServerFunctions.calculationDivide", "ServerFunctions.calculationStart" ]
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

            #print("Local restult: {}".format(server_func.calculated_value))
            print(" = {}".format(server_func.calculated_value))

            for server in server_func.known_server_addr:
                con = xmlrpc.client.ServerProxy(get_con_string(server))
                getattr(con,next_op[0])(*next_op[1])


        if time.time() >= next_calc_time and current_time - start_time < 20:
            calculation_op    = calculations[random.randint(0,len(calculations)-2)]
            calculation_value = random.randint(1, 10)
            calculations_queue.append((calculation_op, [int(calculation_value)]))

            next_calc_time    = random.uniform(rnd_time_lower_bound, rnd_time_upper_bound) + time.time()
        current_time = time.time()



#=======
#def get_next_server(server_func):
#    next_server = None
#    if not server_func.known_server_addr:
#        return next_server # which is None
#    if server_func.got_token_from is None:
#        # start at first element
#        next_server = server_func.known_server_addr[0]
#    else:
#        # get next one
#        next_server_idx = server_func.known_server_addr.index(server_func.got_token_from)+1
#        if next_server_idx >= len(server_func.known_server_addr):
#            # start over
#            next_server_idx = 0
#        next_server = server_func.known_server_addr[next_server_idx]
#    return next_server
#>>>>>>> dev
