import struct
import datetime as dt
from datetime import datetime, date, timedelta


class Util():
    """
    Util

    Contains utility methods for retrieving the server time, packaging outbound messages into
    bytes and unpackaging inbound messages into dictionaries according to the OUCH protocol.
    """

    def get_server_time():
        """
        Returns nanoseconds elasped since midnight - 0 nanoseconds as datetime only has microsecond accuracy.
        the time module has no way of returning the timestamp of midnight.
        """
        seconds = (datetime.now() - datetime.combine(date.today(), dt.min.time())).total_seconds() 
        return seconds / (timedelta(microseconds=1)*1000)

    @staticmethod
    def package_outbound(package: list) -> bytes:
        """
        Package outbound messages from the server into bytes.

        :param package: List of fields and values of outbound message in the
                        order defined by the OUCH protocol.
        :returns: packaged bytes object.
        :raises Exception: Outbound order has not been implemented.
        """
        msg_type = package[0]
        for i in range(len(package)):
            if isinstance(package[i], str):
                package[i] = bytes(package[i], encoding="ascii")
        package = tuple(package)
        format_s = None
        if msg_type == "S": # Server event
            format_s = "!cQc" 
        elif msg_type == "J": # Order rejected
            format_s = "!!cQIc"
        else:
            raise Exception(f"Unrecognised outbound message type {msg_type}")
        return struct.pack(format_s, *package)

    @staticmethod
    def package_inbound(package: list):
        """
        Message should be a list with fields in the order defined in the Japannext OUCH Trading Specification.

        :param package: List of fields and values of an inbound message in the
                        order defined by the OUCH protocol.
        :returns: packaged bytes object of package.
        :raises Exception: Inbound order has invalid header.
        """
        header = package[0]
        for i in range(len(package)):
            if isinstance(package[i], str):
                package[i] = bytes(package[i], encoding="ascii")
        format_s = None
        if header == b'O':
            format_s = "!cI10scIi4siIIccIcc"
            package[7] = int(package[7]*10) # Convert decimal price to integer
        elif header == b'U':
            format_s = "!cIIIiIcI"
            package[4] = int(package[4]*10) # Convert decimal price to integer
        elif header == b'X':
            format_s = "!cII"
        else:
            raise Exception(f"Invalid header '{header}'")
        package = tuple(package) 
        
        return struct.pack(format_s, *package)

    def unpackage_order(header: bytes, body: bytes) -> dict:
        """
        Parse bytes input from the TCP socket into a dictionary output.

        :param header: First byte of an inbound message denoting the order type.
        :param body: Rest of the bytes of an inbound message.
        :returns: Dictionary with fields formatted according to the OUCH protocol.
        :raises Exception: Header is an invalid byte.
        """
        
        message_dict = None 
        if header == b'O' or header == 'O':
            message_dict = Util._unpackage_enter_order(body)
        elif header == b'U' or header == 'U':
            message_dict = Util._unpackage_replace_order(body)
        elif header == b'X' or header == 'X':
            message_dict = Util._unpackage_cancel_order(body)
        else:
            raise Exception(f"Invalid header '{header}'")

        return message_dict

    @staticmethod
    def _unpackage_enter_order(body: bytes):
        """Unpackages an enter order. For internal use only."""
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

    @staticmethod
    def _unpackage_replace_order(body: bytes):
        """Unpackages a replace order. For internal use only."""
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
        msg_dict["price"] /= 10
        for key in msg_dict.keys():
            if isinstance(msg_dict[key], bytes):
                msg_dict[key] = msg_dict[key].decode("ascii").strip()
        
        return msg_dict 

    @staticmethod
    def _unpackage_cancel_order(body: bytes):
        """Unpackages a cancel order. For internal use only."""
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

