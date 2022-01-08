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

# global variable: address + port
defaultAddress = ('localhost', 1007)

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

        self.client_dict = {}
        self.client_dict_lock = threading.Lock()
        self.client_no = 0

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

    def __enter__ (self) -> None:
        """
        enter: (*address, *port)
        """
        # Prepare!.. t h e   s o c k
        self._setup_socket()
        self.connection, self.client = self.socket.accept()
    
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
        self.client_dict[client_id].send(msg)

    def get_queue(self) -> Queue:
        """Returns the message queue."""
        return self.queue

    def get_clients(self) -> dict:
        """Returns the dictionary hashing client_id to their respective socket."""
        return self.client_dict.values()

    def terminate(self):
        """Close all threads and shut down receiver."""
        self.thread_lock.acquire()
        for thread in self.threads:
            thread.join()
        self.thread_lock.release()
        self.daemon_listener.join()
    
    def _setup_socket(self):
        """Bind socket and listen for connections."""
        self.socket.bind(defaultAddress)
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
        self.client_dict[client_id] = connection
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
            except Exception:
                print(f"Connection of client_id {client_id} dropped.")
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

    def __exit__ (self):
        """Closes connection when out of scope."""
        self.connection.close()