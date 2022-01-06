"""
The Ouch Team
TCP/IP Input Receiver
"""

import socket
import common

# global variable: address + port
defaultAddress = ('localhost', 1007)

class dem:
    
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
    - add custom address and port values (optional; not validated)
    """
    def __enter__ (self, address = defaultAddress[0], port = defaultAddress[1]) -> None:

        # Prepare!.. t h e   s o c k
        self.sock.bind(address, port)
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

    
class mo:

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
    enter: (*address, *port)
    - add custom address and port values (optional; not validated)
    """
    def __enter__(self, address = defaultAddress[0], port = defaultAddress[1]) -> None:

        # Prepare!.. t h e   s o c k   I I
        self.sock = socket.create_connection((address, port))
    
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