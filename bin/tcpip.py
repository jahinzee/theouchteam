"""
The Ouch Team
TCP/IP Input Receiver
"""

from bin.common import common


class receiver:

    # imports
    import socket, common

     # class constant: Prepare socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # class constant: Default port, for if ___init___ parameter port is not numeric
    defaultPort = 1007

    # class constant: Store the expected length of each type of message (minus the header byte), along with appropriate header byte
    bodyLengthDict = {
        b'O' : 48,
        b'U' : 26,
        b'X' : 9
    }

    """
    init: (string: address, int: port)
    - returns error if port is not numerical
    """
    def __init__(self, address, port) -> None:

        # Prepare!.. t h e   s o c k
        self.sock.bind((address, port if common.isInt(port) else self.defaultPort))
        self.sock.listen(1)
        self.connection, self.client = self.sock.accept()

    """
    get() -> (bytearray: header, bytearray: body)
    - body is appropriately sized to match the header, according to Japannext OUCH Specs.
    - all illegal headers are returned with a single null byte as body.
    """
    def get(self):

        try:

            # Stores header byte
            header = self.connection.recv(1)

            # Calculates expected size of body, using bodyLengthDict
            bodyLength = 0
            for byte in self.bodyLengthDict:
                if header == byte:
                    bodyLength = self.bodyLengthDict[byte]

            # grab body,
            body = self.connection.recv(bodyLength) if bodyLength != 0 else 0x00

            # output
            return(header, body)

        finally:

            # Close connection
            self.connection.close()