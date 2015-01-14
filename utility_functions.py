from xmlrpc.server  import SimpleXMLRPCServer
import re

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
