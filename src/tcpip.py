"""
The Ouch Team
TCP/IP Input Receiver

Use with, uh, "with" block, similar to how its used in file manipulation:

>>> with receiver() as r:
...     r.getBytestream()
...     # insert code here

With this, excess port bandwidth is not taken up, as connection cleanly closes once it is out of scope.



THERE IS PROBABLY BUGS IN THIS :(

"""

import socket
import common

# global variable: address + port
defaultAddress = ('localhost', 1007)

class receiver:
    
     # class constant: Prepare socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # class constant: Store the expected length of each type of message (minus the header byte), along with appropriate header byte
    bodyLengthDict = {
        b'O' : 47,  # ENTER
        b'U' : 25,  # REPLACE
        b'X' : 8,   # CANCEL
    }

    """
    enter: (*address, *port)
    """
    def __enter__ (self) -> None:

        # Prepare!.. t h e   s o c k
        self.sock.bind(defaultAddress)
        self.sock.listen(1)
        self.connection, self.client = self.sock.accept()
        


    """
    getBytestream() -> (bytearray: header, bytearray: body)
    - body is appropriately sized to match the header, according to Japannext OUCH Specs.
    - all illegal headers are returned with a single null byte as body.
    """
    def getBytestream (self):

        # Store header byte
        header = self.connection.recv(1)

        # Calculates expected size of body, using bodyLengthDict
        bodyLength = 0
        for byte in self.bodyLengthDict:
            if header == byte:
                bodyLength = self.bodyLengthDict[byte]

        # grab body,
        body = self.connection.recv(bodyLength) if bodyLength != 0 else 0x00

        # output
        return (header + body)

    """
    exit:
    - closes connection when out of scope
    """
    def __exit__ (self):
        self.connection.close()

    
class sender:

    # class constant: Prepare socket variable
    socket = None

    # class constant: Store the expected length of each type of message (minus the header byte), along with appropriate header byte
    bodyLengthDict = {
        b'S' : 9,   # EVENT
        b'A' : 64,  # ACCEPTED
        b'U' : 51,  # REPLACED
        b'C' : 17,  # CANCELLED
        b'D' : 26,  # AIQ CANCELLED
        b'E' : 29,  # EXECUTED
        b'J' : 12,  # REJECTED
    }
    
    """
    enter:
    """
    def __enter__(self) -> None:

        # Prepare!.. t h e   s o c k   I I
        self.sock = socket.create_connection(defaultAddress)
    
    """
    sendBytestream(bytearray: header, bytearray: body)
    - illegal headers are caught with exceptions
    """
    def sendBytestream (self, header, body):

        # Calculates expected size of body, using bodyLengthDict, and validate
        bodyLength = 0
        for byte in self.bodyLengthDict:
            if header == byte:
                bodyLength = self.bodyLengthDict[byte]
        
        # Catch invalid header
        if bodyLength == 0:
            return ValueError("Invalid header byte")
        
        # Catch illegal length
        if bodyLength != len(body):
            return ValueError("Illegal length; refer to Japannext OUCH Documentation")

        # Join header and body
        header.extend(body)

        # Sends byte to port
        self.sock.sendall(bytes)
    
    """
    exit:
    - closes connection when out of scope
    """
    def __exit__ (self):
        self.sock.close()