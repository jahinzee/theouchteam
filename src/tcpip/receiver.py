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
import common
import threading
from queue import Queue

# global variable: address + port
defaultAddress = ('localhost', 1007)

class receiver:

    # class constant: Store the expected length of each type of message (minus the header byte), along with appropriate header byte
    BODY_LENGTH_DICT = {
        b'O' : 47,  # ENTER
        b'U' : 25,  # REPLACE
        b'X' : 8,   # CANCEL
    }

    def __init__(self):
        # Prepare socket
        self.queue = Queue() # Message queue which will be retrieved by the exchange

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._setup_socket()
        self.client_dict = {}
        self.client_dict_lock = threading.Lock()
        self.client_no = 0
        self.threads = []
        self.thread_lock = threading.Lock()
        self.daemon_listener = threading.Thread(
            name = "daemon",
            target = lambda: self.receive_connections_thread(),
            daemon = True
        )

    """
    enter: (*address, *port)
    """
    def __enter__ (self) -> None:
        # Prepare!.. t h e   s o c k
        self._setup_socket()
        self.connection, self.client = self.socket.accept()
    
    def _setup_socket(self):
        self.socket.bind(defaultAddress)
        self.socket.listen(1)

    def terminate(self):
        self.thread_lock.acquire()
        for thread in self.threads:
            thread.join()
        self.thread_lock.release()
        self.daemon_listener.join()

    def receive_connections_thread(self):
        while True:
            self._receive_connections()

    def _receive_connections(self):
        connection, addr = self.socket.accept()
        client_id = hash((addr, self.client_no))
        self.client_dict[client_id] = connection
        self.queue.put({
            "type": "C",
            "id": client_id
        })
        client = threading.Thread(
            name = "client"+str(self.client_no), 
            target = lambda: self.handle_client(connection, client_id),
            daemon = True
        )
        self.thread_lock.acquire()
        self.threads.append(client)
        self.thread_lock.release()
        self.client_no += 1

    """
    handle_client

    Listens to the client and puts any well formatted byte message into the queue.
    """
    def handle_client(self, connection, client_id):
        while True:
            try:
                header, body = self.receive_bytes(connection)
                if body != 0x00:
                    self.queue.put({
                        "type": "M", # Message
                        "id": client_id, 
                        "header": header,
                        "body": body
                    })
            except OSError():
                print(f"Connection of client_id {client_id} dropped.")
                break
    
    """
    send_message

    Sends a byte message to the connection hashed to by the client_id.
    """
    def send_message(self, client_id, msg):
        self.client_dict[client_id].send(msg)

    def get_queue(self):
        return self.queue

    def get_clients(self):
        return self.client_dict.values()

    """
    receive_bytes() -> (bytearray: header, bytearray: body)
    - body is appropriately sized to match the header, according to Japannext OUCH Specs.
    - all illegal headers are returned with a single null byte as body.
    """
    def receive_bytes(self, connection):
        # Store header byte
        header = connection.recv(1)

        # Calculates expected size of body, using bodyLengthDict
        bodyLength = 0
        for byte in self.bodyLengthDict:
            if header == byte:
                bodyLength = self.bodyLengthDict[byte]

        # grab body,
        body = connection.recv(bodyLength) if bodyLength != 0 else 0x00

        # output
        return header, body

    """
    exit:
    - closes connection when out of scope
    """
    def __exit__ (self):
        self.connection.close()