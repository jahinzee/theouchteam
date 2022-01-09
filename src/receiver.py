"""
The Ouch Team
TCP/IP Input Receiver

Use with, uh, "with" block, similar to how its used in file manipulation:

>>> with receiver() as r:
...     r.getBytestream()
...     # insert code here


With this, excess port bandwidth is not taken up, as connection cleanly closes once it is out of scope.

THERE IS PROBABLY BUGS IN THIS :(

##
Receiver class has been modified to include an __init__ method so that it can be more easily integrated
with the exchange.
##
"""
import socket
import threading
from queue import Queue
import pprint
import configparser

from src.util import Util

class Receiver():

    # class constant: Store the expected length of each type of message (minus the header byte), along with appropriate header byte
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

    def __init__(self):
        """
        This class accepts connections from multiple clients by spawning a new thread
        whenever a client connects to the socket. On initialisation, this class will
        immediately spawn a darmon listener which continuously listens for threads.

        Messages from the client will be placed into a shared queue, which can be retrieved
        by a context which calls the get_queue function.
        """
        # Message queue which will be retrieved by the exchange
        self.queue = Queue() 

        # Prepare socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._setup_socket()

        # {client_id: socket}
        self.client_dict = {}
        self.client_dict_lock = threading.Lock()
        self.client_no = 0

        # List of all messages received by the server socket in sequence - for debugging.
        self.message_log_lock = threading.Lock()
        self.message_log = []

        # List of connections and disconnections - for debugging.
        self.connection_log_lock = threading.Lock()
        self.connection_log = []

        # List of client Thread objects.
        self.threads = []
        self.thread_lock = threading.Lock()

        # Daemon thread which listens for and accepts connections.
        self.daemon_listener = threading.Thread( 
            name = "daemon",
            target = lambda: self._receive_connections_thread(),
            daemon = True
        )
        self.daemon_listener.start()
    
    def send_message(self, client_id: int, msg: bytes):
        """
        Sends a byte message to the connection hashed to by the client_id.
        """
        header = msg[0:1]
        if header in self.BODY_LENGTH_DICT.keys():
            if len(msg)-1 != self.BODY_LENGTH_DICT[header]:
                raise ValueError(f"Message {msg} has invalid length {len(msg)}")
        else:
            raise ValueError(f"Sending message with invalid header '{header}'")
        self.client_dict_lock.acquire()
        self.client_dict[client_id].send(msg)
        self.client_dict_lock.release()

    def get_queue(self) -> Queue:
        """Returns the message queue."""
        return self.queue
    
    def print_log(self):
        """Prints the sequence of messages received by the server."""
        self.message_log_lock.acquire()
        print("-----------")
        print("Message Log")
        print("-----------")
        pprint.pprint(self.message_log)
        self.message_log_lock.release()
        print("Address: " + str(self.DEFAULT_ADDRESS))
    
    def print_connections(self):
        """Prints the log of connections to and disconnections from the server."""
        self.connection_log_lock.acquire()
        print("--------------")
        print("Connection Log")
        print("--------------")
        for event in self.connection_log:
            print(event)
        self.connection_log_lock.release()

    def terminate(self):
        """Close all threads and shut down receiver."""
        self.client_dict_lock.acquire()
        for conn in self.client_dict.values():
            conn.close()
        self.client_dict_lock.release()
        self.thread_lock.acquire()
        for thread in self.threads:
            thread.join()
        self.thread_lock.release()
    
    def _setup_socket(self):
        """Bind socket and listen for connections."""
        host, port = Util.get_addr()
        self.socket.bind((host, port))
        self.socket.listen(100)

    def _receive_connections_thread(self):
        """Wrapper function for threading _receive_connections."""
        while True:
            self._receive_connections()

    def _receive_connections(self):
        """
        Daemon thread spawning a new thread whenever a client connects. Also
        assigns a client id to each connection.
        """
        connection, addr = self.socket.accept()
        client_id = hash((addr, self.client_no))

        self.client_dict_lock.acquire()
        self.client_dict[client_id] = connection
        self.client_dict_lock.release()

        self.connection_log_lock.acquire()
        self.connection_log.append(f"{Util.get_server_time()}: client_id {client_id} connected.")
        self.connection_log_lock.release()

        self.queue.put({
            "type": "C",
            "id": client_id
        })
        client = threading.Thread(
            name = "client"+str(self.client_no), 
            target = lambda: self._handle_client(connection, client_id),
            daemon = True
        )
        client.start()

        self.thread_lock.acquire()
        self.threads.append(client)
        self.thread_lock.release()

        self.client_no += 1

    def _handle_client(self, connection, client_id):
        """
        Listens to the client and puts any non-empty byte message into the queue.
        A new thread running handle_client is spawned whenever the receiver accepts
        a new connection.
        """
        while True:
            try:
                header, body = self._receive_bytes(connection)
                if body != 0x00:
                    self.queue.put({
                        "type": "M", # Message
                        "id": client_id, 
                        "header": header,
                        "body": body
                    })
                    self.message_log_lock.acquire()
                    self.message_log.append(["id: " + str(client_id), header + body])
                    self.message_log_lock.release()
            except Exception:
                self.connection_log_lock.acquire()
                self.connection_log.append(f"{Util.get_server_time()}: client_id {client_id} disconnected.")
                self.connection_log_lock.release()
                break

    def _receive_bytes(self, connection: socket): # -> (bytes, bytes):
        """
        Body is appropriately sized to match the header, according to Japannext OUCH Specs.
        All illegal headers are returned with a single null byte as body.
        """
        # Store header byte
        header = connection.recv(1)

        # Calculates expected size of body, using bodyLengthDict
        body_length = 0
        if header in self.BODY_LENGTH_DICT.keys():
            body_length = self.BODY_LENGTH_DICT[header]
        else:
            raise ValueError(f"Invalid header type '{header}'")

        # grab body,
        body = connection.recv(body_length) if body_length != 0 else 0x00

        # output
        return header, body