
"""
The Sock Team
Client

Client for connecting to the receiver.
"""
import socket
import common

# global variable: address + port
defaultAddress = ('localhost', 1007)

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