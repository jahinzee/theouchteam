
import json
from util import Util

# Testing inputs
if __name__ == "__main__":
    # Testing Place order
    vals = [
        b'O', 
        1234,
        b"Claire    ", # This must be 10 characters. Fill the unused characters with spaces.
        b'B',
        345624,
        1234,
        b"DAY ", # This must be 4 characters.
        500000.5, # Price  = $500000.5
        99999,
        5834,
        b"P",
        b"P",
        1234,
        b'1',
        b'1'
    ]

    b = Util.package(vals)
    msg_dict = Util.unpackage(b[0:1], b[1:]) # Separate header byte from rest of the bytes.
    print(json.dumps( # Make the dictionary easy to read
        msg_dict,
        indent = 4,
        separators = (',', ': ')
    ))

    # Testing replace order
    vals = [
        b'U',
        1234,
        1235,
        100000,
        5000.5,
        0,
        b" ",
        555
    ]

    b = Util.package(vals)
    msg_dict = Util.unpackage(b[0:1], b[1:])
    print(json.dumps( # Make the dictionary easy to read
        msg_dict,
        indent = 4,
        separators = (',', ': ')
    ))

    # Testing Cancel Order
    vals = [
        b'X',
        1234,
        0
    ]

    b = Util.package(vals)
    msg_dict = Util.unpackage(b[0:1], b[1:])
    print(json.dumps( # Make the dictionary easy to read
        msg_dict,
        indent = 4,
        separators = (',', ': ')
    ))