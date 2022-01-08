
"""
The Sock Team
Client

Client for connecting to the receiver.
"""
import sys
import socket
import threading
from queue import Queue
import json

from util import Util

# global variable: address + port
defaultAddress = ('localhost', 1007)

class Client():
    """
    Client

    Previously "sender" for sending messages to the receiver via the TCPIP protocol. 
    Modified to be an interface for the client to input data to the exchange. Exchange.py
    must be initialised on the local machine before initialising Client, otherwise the connection
    will fail. 
    """

    # class constant: Store the expected length of each type of message (minus the header 
    # byte), along with appropriate header byte
    BODY_LENGTH_DICT = {
        b'O' : 47,  # ENTER
        b'U' : 25,  # REPLACE
        b'X' : 8,   # CANCEL
        b'S' : 9,   # EVENT
        b'A' : 64,  # ACCEPTED
        b'U' : 51,  # REPLACED
        b'C' : 17,  # CANCELLED
        b'D' : 26,  # AIQ CANCELLED
        b'E' : 29,  # EXECUTED
        b'J' : 13,  # REJECTED
    }
    
    def __enter__(self) -> None:
        """enter:"""
        # Prepare!.. t h e   s o c k   I I
        self.socket = self._connect()
    
    def user_input(self):
        pass

    def __init__(self, path=None):
        """
        Prepare the client connection.
        """
        # Connect to the receiver.
        self.socket = self._connect()

        # Queue for receiving messages from the exchange.
        self.queue = Queue()

        # Event to terminate the client.
        self.terminated = threading.Event()

        # Initialise thread for receiving and outputting messages received from the exchange.
        self.listener = threading.Thread(
            name = "listener", 
            target = lambda: self._listen_thread(),
            daemon = True
        )
        self.listener.start()

        # Take and parse user input, then send to the exchange.
        actions = []
        if path != None:
            with open(path, "r") as json_f:
                data = json.load(json_f)
                for action in data["actions"]:
                    actions.append(list(action.values()))
        while True:
            try:
                if len(actions) == 0:
                    package = self.user_input()
                else:
                    action = actions.pop(0)
                    package = Util.package(action)
                self._sendBytestream(package[0:1], package[1:])
                input()
            except KeyboardInterrupt:
                self.terminated.set()
                print("Client Main Thread Interrupted")
                break
            except ConnectionResetError:
                print("Server Disconnected")
                break
    

    
    def _listen_thread(self):
        while not self.terminated.is_set():
            self._listen()
        print("Client listener thread terminating.")
    
    def _listen(self):
        header, body = self._receive_bytes()
        msg_dict = Util.unpackage(header, body)
        print(json.dumps(
            msg_dict,
            indent = 4,
            separators = (",", ": ")
        ))

    def _receive_bytes(self):
        # Store header byte
        header = self.socket.recv(1)

        # Calculates expected size of body, using bodyLengthDict
        body_length = 0
        if header in self.BODY_LENGTH_DICT.keys():
            body_length = self.BODY_LENGTH_DICT[header]
        else:
            raise ValueError(f"Invalid header type '{header}'")

        # grab body,
        body = self.socket.recv(body_length) if body_length != 0 else 0x00

        # output
        return header, body
    
    def _sendBytestream(self, header: bytes, body: bytes):
        """
        Illegal headers are caught with exceptions
        """
        # Calculates expected size of body, using bodyLengthDict, and validate
        body_length = 0
        if header in self.BODY_LENGTH_DICT.keys():
            body_length = self.BODY_LENGTH_DICT[header]
        else:
            raise ValueError(f"Invalid header byte {header}")
        
        # Catch illegal length
        if body_length != len(body) and header != b'U':
            raise ValueError(f"Illegal length {body_length} for header '{header}'")

        # Join header and body
        msg = header + body

        # Sends byte to port
        self.socket.sendall(msg)

    def _connect(self):
        self.socket = socket.create_connection(defaultAddress)
        return self.socket
    
    def __exit__ (self):
        """closes connection when out of scope"""
        self.socket.close()

if __name__ == "__main__":
    if len(sys.argv) == 2:
        orderlist_path = sys.argv[1]
    else:
        orderlist_path = None
    Client(path=orderlist_path)