__author__ = 'AMelnyk'
import xmlrpc.client
import time
import random
import threading
import utility_functions as utils


class RicartAgrawalaAlgorithm:
    def __init__(self, server_functions):
        self.server_functions = server_functions
        self.calculations_generator_thread = None
        self.run_thread = None

    def send_request(self):
        if self.server_functions.calc_queue and not self.server_functions.request_sent:
            self.server_functions.received_replies_servers = []
            # increment clock counter
            self.server_functions.clock_timestamp += 1
            # send request to all servers
            for server in self.server_functions.known_server_addr:
                con = xmlrpc.client.ServerProxy(utils.get_con_string(server))
                print("Send request to {}".format(server))
                thread = threading.Thread(target=con.requestAccess,
                                          args=(self.server_functions.id, self.server_functions.clock_timestamp),
                                          daemon=True,
                                          name="send_request")
                thread.start()
            self.server_functions.request_sent = True

            # check if we got replies from all servers, the result set must be empty
            while set(self.server_functions.known_server_addr) - set(self.server_functions.received_replies_servers):
                # wait
                time.sleep(0.01)
            print("Received all replies")
            # we got all replies, perform the calculation
            self.perform_own_calculation()
        self.server_functions.request_sent = False

    def perform_own_calculation(self):
        if self.server_functions.calc_queue:
            # we take the current length of the own calc queue as index, the number of operations to perform
            index = len(self.server_functions.calc_queue)
            self.server_functions.clock_timestamp += 1
            for server in self.server_functions.known_server_addr:
                con = xmlrpc.client.ServerProxy(utils.get_con_string(server))
                # tell others to perform my calculations
                con.performRemoteCalculations(index, self.server_functions.id)
            self.server_functions.performOwnCalculations(index)
            # send ok reply to other servers
            for server in self.server_functions.reply_to_server_queue:
                self.server_functions.sendReply(server)
                self.server_functions.reply_to_server_queue.remove(server)

    def start(self, starter):
        # self.server_functions.clock_timestamp = random.randint(1, 1000 * len(self.server_functions.known_server_addr))
        if starter:
            value = random.randint(1, 10)
            # generate a random value and start the calculation
            self.server_functions.start(value, starter)
        self.run_thread = threading.Thread(target=self.run, daemon=True, name="main_run")
        self.run_thread.start()

    def run(self):
        # init logical clock, take a value between 1 and 2* number of nodes in the network
        self.calculations_generator_thread = threading.Thread(target=self.generate_calculation, daemon=True,
                                                              name="calc_generator")
        self.calculations_generator_thread.start()
        start_time = time.time()
        while time.time() - start_time < 20 or self.server_functions.calc_queue:
            if not self.server_functions.request_sent:
                self.send_request()
        self.calculations_generator_thread.join()
        print("Caclulation is over, result: {}".format(self.server_functions.calculated_value))

    def generate_calculation(self):
        calculations = ["ServerFunctions.calculationSum",
                        "ServerFunctions.calculationSubtract",
                        "ServerFunctions.calculationMultiply",
                        "ServerFunctions.calculationDivide",
                        "ServerFunctions.calculationStart"]
        rnd_time_lower_bound = utils.sec_to_msec(800)
        rnd_time_upper_bound = utils.sec_to_msec(1000)
        total_running_time = 20
        start_time = time.time()
        operation_count = 1
        while time.time() - start_time < total_running_time:
            # generate new calculation
            calculation_op = calculations[random.randint(0, len(calculations) - 2)]
            calculation_value = random.randint(1, 9)
            calculation = (calculation_op, [int(calculation_value)], operation_count)
            print("Generated own calculation {} {}".format(calculation[0], calculation[1]))
            self.server_functions.calc_queue.append(calculation)
            # increment operation counter
            operation_count += 1
            # send calculations
            for server in self.server_functions.known_server_addr:
                con = xmlrpc.client.ServerProxy(utils.get_con_string(server))
                con.queueOperation(self.server_functions.id, calculation)
            time.sleep(random.uniform(rnd_time_lower_bound, rnd_time_upper_bound))