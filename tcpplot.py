import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time
import socket
import json
import threading

class ClientThread(threading.Thread):

    def __init__(self, address, clientsocket):

        threading.Thread.__init__(self)
        self.address = address
        self.clientsocket = clientsocket
        self.skmf = clientsocket.makefile(mode='r')
        print("[+] New thread for %s" % (self.address, ))

    def run(self): 
   
        print("Connected : %s" % (self.address, ))
        while True:
#            r = self.clientsocket.recv(4096)
            r = self.skmf.readline()
#            print("Read : " + str(r))
            if len(r) == 0:
                break
            values = json.loads(r)
            print("Got " + str(len(values)) + " channels, " + str(len(values[0])) + " values")
            plt.clf()
            plt.axis([0, len(values[0]), -0.1, 1])
            for channel in range(0, len(values)):
                plt.plot(np.array(values[channel]))
            plt.pause(0.001)
        print("Disconnected : %s" % (self.address, ))


# create an INET, STREAMing socket
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind the socket to a public host, and a well-known port
serversocket.bind(("0.0.0.0", 1088))
# become a server socket
print("[ ] Waiting for a client..")
serversocket.listen(5)

plt.ion()

while True:
    # accept connections from outside
    print("[ ] Waiting for a client.. at accept()")
    (clientsocket, address) = serversocket.accept()
    print ("Incoming : " + str(address))
    # now do something with the clientsocket
    # in this case, we'll pretend this is a threaded server
    ct = ClientThread(address, clientsocket)
    ct.run()

