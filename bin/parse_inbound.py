"""
The Ouch Team
Utility module to parse inbound client messages 
"""

import struct
import json


body_length_dict = {
    b'O' : 47,
    b'U' : 25,
    b'X' : 8
}

# 0 = Alpha
# 1 = Integer


def parse_enter_order(body):
    """
    message_dict = {
        "message_type": (0, 1, 0), # (offest, length, type)
        "order_token": (1, 4, 1),
        "client_reference": (5, 10, 0),
        "buy_sell_indicator": (15, 1, 0),
        "quantity": (16, 4, 1),
        "orderbook_id": (20, 4, 1),
        "group": (24, 4, 0),
        "price": (28, 4, 1),
        "time_in_force": (32, 4, 1),
        "firm_id": (36, 4, 1),
        "display": (40, 1, 0),
        "capacity": (41, 1, 0),
        "minimum_quantity": (42, 4, 1),
        "order_classification": (46, 1, 0),
        "cash_margin_type": (47, 1, 0)
    }

    for name, info in message_dict.items():
        offset = info[0]
        length = info[1]
        field_type = info[2]
        if field_type == 0: # Alpha
            message_dict[name] = body[offset:offset+length].decode(encoding='ascii')
        elif field_type == 1: # Integer
    """
    names = (
        "message_type",
        "order_token",
        "client_reference",
        "buy_sell_indicator",
        "quantity",
        "orderbook_id",
        "group",
        "price",
        "time_in_force",
        "firm_id",
        "display",
        "capacity",
        "minimum_quantity",
        "order_classification",
        "cash_margin_type"
    )
    format_s = "!I10scIi4siIIccIcc"
    fields = ('O',) + struct.unpack(format_s, body)
    msg_dict = dict(zip(names, fields))
    msg_dict["price"] /= 10
    for key in msg_dict.keys():
        if isinstance(msg_dict[key], bytes):
            msg_dict[key] = msg_dict[key].decode("ascii").strip()

    return msg_dict


def parse_replace_order(body):
    """
    message_dict = {
        "message_type": (0, 1, 0),
        "existing_order_token": (1, 4, 1),
        "replacement_order_token": (5, 4, 1),
        "quantity": (9, 4, 1),
        "price": (13, 4, 1),
        "time_in_force": (17, 4, 1),
        "display": (21, 1, 0),
        "minimum_quantity": (22, 4, 1)
    }
    """
    names = (
        "message_type",
        "existing_order_token",
        "replacement_order_token",
        "quantity",
        "price",
        "time_in_force",
        "display",
        "minimum_quantity"
    )
    format_s = "!IIIiIcI"
    fields = ('U',) + struct.unpack(format_s, body)
    msg_dict = dict(zip(names, fields))
    msg_dict ["price"] /= 10
    for key in msg_dict.keys():
        if isinstance(msg_dict[key], bytes):
            msg_dict[key] = msg_dict[key].decode("ascii").strip()
    
    return msg_dict 


def parse_cancel_order(body):
    """
    message_dict = {
        "message_type": (0, 1, 0),
        "order_token": (1, 4, 1),
        "quantity": (5, 4, 1)
    }
    """
    names = (
        "message_type",
        "order_token",
        "quantity"
    )
    format_s = "!II"
    fields = ('X',) + struct.unpack(format_s, body)
    msg_dict= dict(zip(names, fields))
    for key in msg_dict.keys():
        if isinstance(msg_dict[key], bytes):
            msg_dict[key] = msg_dict[key].decode("ascii").strip()

    return msg_dict


def parse(header, body):
    length = -1
    if header not in body_length_dict.keys():
        print(f"Invalid header {header}")
        return
    else:
        length = body_length_dict[header]
    
    message_dict = None 
    if header == b'O':
        message_dict = parse_enter_order(body)
    elif header == b'U':
        message_dict = parse_replace_order(body)
    else:
        message_dict = parse_cancel_order(body)
    return message_dict


"""
pack_message

Message should be a tuple with fields in the order defined in the
Japannext OUCH Trading Specification.

The price field should an integer, calculated using the formula price_field = int(price*10).
Alpha fields should be a bytes object representing a string or character i.e: Use b'Python' instead of 'Python' 
"""
def pack_message(msg):
    header = msg[0]
    format_s = None
    if header == b'O':
        format_s = "!cI10scIi4siIIccIcc"
    elif header == b'U':
        format_s = "!cIIIiIcI"
    elif header != b'X':
        format_s = "!cII"
    else:
        print("Invalid Message Header")
        return
    
    return struct.pack(format_s, *msg)


# Testing inputs
if __name__ == "__main__":
    vals = (
        b'O', 
        1234,
        b"Claire    ", # This must be 10 characters. Fill the unused characters with spaces.
        b'B',
        345624,
        1234,
        b"DAY ", # This must be 4 characters.
        5000005, # Price  = $500000.5
        99999,
        5834,
        b"P",
        b"P",
        1234,
        b'1',
        b'1'
    )

    b = pack_message(vals)
    msg_dict = parse(b'O', b[1:]) # Separate header byte from rest of the bytes.
    print(json.dumps( # Make the dictionary easy to read
        msg_dict,
        indent = 4,
        separators = (',', ': ')
    ))