from xmlrpc.server  import SimpleXMLRPCServer
import xmlrpc.client
import time
import re
import random

def sec_to_msec(sec):
    return sec/1000.0

def translate_timing_to_tuple(timing_string):
    if re.match('[Ss]low',timing_string):
        return (sec_to_msec(2000), sec_to_msec(5000), sec_to_msec(200))
    elif re.match('[Nn]ormal',timing_string):
        return (sec_to_msec(500), sec_to_msec(2000), sec_to_msec(100))
    elif re.match('[Ff]ast',timing_string):
        return (sec_to_msec(20), sec_to_msec(50), sec_to_msec(50))
    raise ValueError

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
    except:
        print("Not foreseen shutdown")
    print("... and offline!")

def get_addr_string(addr, port):
    return "{}:{}".format(addr,port)

def get_con_string(server):
    return "http://{}/".format(server)

# get next server in list
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
        # check if the server is still in the list
        if server_func.got_token_from in server_func.known_server_addr:
            next_server_idx = server_func.known_server_addr.index(server_func.got_token_from)+1
        else:
            # otherwise restart at any known server
            next_server_idx = 0

    # get next one
    if next_server_idx >= len(server_func.known_server_addr):
        # start over
        next_server_idx = 0
    next_server = server_func.known_server_addr[next_server_idx]

    return (next_server, next_server_idx)

def generate_calculations(server_func, calculations_queue, timing_tuple):
    calculations = [ "ServerFunctions.calculationSum",
            "ServerFunctions.calculationSubtract",
            "ServerFunctions.calculationMultiply",
            "ServerFunctions.calculationDivide",
            "ServerFunctions.calculationStart" ]
    rnd_time_lower_bound = timing_tuple[0]
    rnd_time_upper_bound = timing_tuple[1]
    total_running_time = 20
    min_wait_time = 0.001
    start_time = time.time()
    current_time = time.time()
    iteration = 0

    next_calc_time = random.uniform(rnd_time_lower_bound, rnd_time_upper_bound) + time.time()
    while current_time - start_time < total_running_time or len(calculations_queue)>0:
        time.sleep(min_wait_time)
        if server_func.got_token and not server_func.token_on_way_to_next_server and len(calculations_queue) > 0:
            server_func.keep_token = True
            next_op = calculations_queue.pop(0)

            print("Local: ", end="")
            if re.search("Start",next_op[0]):
                server_func.calculationStart(next_op[1][0],False)
            elif re.search("Sum",next_op[0]):
                server_func.calculationSum(next_op[1][0])
            elif re.search("Subtract",next_op[0]):
                server_func.calculationSubtract(next_op[1][0])
            elif re.search("Multiply",next_op[0]):
                server_func.calculationMultiply(next_op[1][0])
            elif re.search("Divide",next_op[0]):
                server_func.calculationDivide(next_op[1][0])

            for server in server_func.known_server_addr:
                entry_time = time.time()*1000
                con = xmlrpc.client.ServerProxy(get_con_string(server))
                ret_val = getattr(con,next_op[0])(*next_op[1])
                exit_time = time.time()*1000
                iteration = iteration + 1

            server_func.keep_token = False

        if time.time() >= next_calc_time and current_time - start_time < 20:
            calculation_op    = calculations[random.randint(0,len(calculations)-2)]
            calculation_value = random.randint(1, 10)
            calculations_queue.append((calculation_op, [int(calculation_value)]))
            next_calc_time    = random.uniform(rnd_time_lower_bound, rnd_time_upper_bound) + time.time()
        current_time = time.time()

