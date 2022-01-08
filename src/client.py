
"""
The Sock Team
Client

Client for connecting to the receiver.
"""
import socket
import threading
from queue import Queue
import json

from src.util import Util

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

    DEFAULT_ADDRESS = ('localhost', Util.get_port())
    
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
        # Convert all input numbers into unsigned 4-byte integers.
        for action in actions:
            for i in range(len(action)):
                if isinstance(action[i], int):
                    action[i] = Util.unsigned_int(action[i])

        while True:
            try:
                if len(actions) == 0:
                    return
                    package = self.user_input()
                else:
                    action = actions.pop(0)
                    print("Sending: " + str(action))
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
        print("Exchange: " + json.dumps(
            msg_dict,
            indent = 4,
            separators = (",", ": ")
        ) + "\n")

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
        print("Connecting on address " + str(self.DEFAULT_ADDRESS))
        self.socket = socket.create_connection(self.DEFAULT_ADDRESS)
        return self.socket