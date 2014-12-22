from xmlrpc.server  import SimpleXMLRPCServer

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


