import socket
import os
import threading
from threading import Thread
from time import sleep
import parser
from importlib import reload
import sys

# Client ---> Proxy ---> Server
class Game2Proxy(Thread):
    def __init__(self):
        super(Game2Proxy, self).__init__()
        self.daemon = True

        self.ip = "localhost"
        self.port = 25566
        self.proxyserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.fowardto = None  # Proxyclient socket

        self.proxyserver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.proxyserver.bind((self.ip, self.port))
        self.proxyserver.listen(1)

        self.client, self.addr = self.proxyserver.accept()
        sleep(1)

    def run(self):
        while True:
            try:
                data = self.client.recv(16384)
                self.fowardto.sendall(data)
                reload(parser)
                parser.parse(data, "client")
            except ConnectionResetError as cre:
                print("Connection Reset Errror")
            except BrokenPipeError as bpe:
                print("Broken Pipe Error G2P")
            except Exception as ex:
                print("[S-->P] Parser error: {0}".format(ex))


# Client <--- Proxy <--- Server
class Proxy2Server(Thread):
    def __init__(self):
        super(Proxy2Server, self).__init__()
        self.daemon = True

        self.server_ip = "localhost"
        self.server_port = 25565
        self.proxyclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.fowardto = None  # Client socket

    def run(self):
        while True:
            self.proxyclient.connect((self.server_ip, self.server_port))
            while True:
                if self.fowardto is not None:
                    try:
                        data = self.proxyclient.recv(4096)
                        self.fowardto.sendall(data)
                        parser.parse(data, "server")
                    except ConnectionResetError as cre:
                        print("Connection Reset Errror")
                    except BrokenPipeError as bpe:
                        print("Broken Pipe Error P2S")
                    except Exception as ex:
                        print("[S-->P] Parser error: {0}".format(ex))


def main():
    print("Setting up")
    pts = Proxy2Server()
    print("Waiting for a client")
    gtp = Game2Proxy()
    print("Client connected")
    sleep(0.5)
    pts.fowardto = gtp.client
    gtp.fowardto = pts.proxyclient
    gtp.start()
    pts.start()
    print("Setup finished")
    while True:
        if gtp.client is None:
            print("Client disconnected")
        try:
            inp = input("$ ")
            print(inp)
        except KeyboardInterrupt as kbi:
            print("Keyboard Interrupt Exception, shutting down")
            sys.exit(0)


if __name__ == "__main__":
    main()