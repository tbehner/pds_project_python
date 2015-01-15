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
def get_next_server(server_func):
    next_server = None
    if not server_func.known_server_addr:
        return next_server # which is None
    if server_func.got_token_from is None:
        # start at first element
        next_server = server_func.known_server_addr[0]
    else:
        # get next one
        next_server_idx = server_func.known_server_addr.index(server_func.got_token_from)+1
        if next_server_idx >= len(server_func.known_server_addr):
            # start over
            next_server_idx = 0
        next_server = server_func.known_server_addr[next_server_idx]
    return next_server
