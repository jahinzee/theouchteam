from datetime import datetime, date, timedelta
import struct
import configparser


class Util():
    """
    Util

    Contains utility methods for retrieving the server time, packaging outbound messages into
    bytes and unpackaging inbound messages into dictionaries according to the OUCH protocol.
    """
    @staticmethod
    def get_server_time():
        """
        Returns nanoseconds elasped since midnight - 0 nanoseconds as datetime only has microsecond accuracy.
        the time module has no way of returning the timestamp of midnight.
        """
        seconds = (datetime.now() - datetime.combine(date.today(), datetime.min.time())).total_seconds() 
        return int(1000*seconds / (timedelta(microseconds=1).total_seconds()))

    @staticmethod
    def package(package: list):
        """
        Message should be a list with fields in the order defined in the Japannext OUCH Trading Specification.

        :param package: List of fields and values of a message in order defined by the OUCH protocol.
        :returns: packaged bytes object of package.
        :raises Exception: Inbound order has invalid header.
        """
        for i in range(len(package)):
            if isinstance(package[i], str):
                package[i] = bytes(package[i], encoding="ascii")
        header = package[0]
        format_s = None
        if header == b'O': # Place Order
            format_s = "!cI10scII4sIIIccIcc"
            package[7] = int(package[7]*10) # Convert decimal price to integer
        elif header == b'U':
            if len(package) == 14: # Order Replacecd
                package[7] = int(package[7]*10) # Convert decimal price to integer
                format_s = "!cQIcII4sIIcQIcI"
            else: # Replace Order
                package[4] = int(package[4]*10) # Convert decimal price to integer
                format_s = "!cIIIIIcI"
        elif header == b'X': # Cancel Order
            format_s = "!cII"
        elif header == b"S": # Server event
            format_s = "!cQc" 
        elif header == b"J": # Order rejected
            format_s = "!cQIc"
        elif header == b'A': # Order Accepted
            format_s = "!cQI10scII4sIIIccQIccc"
        elif header == b'C': # Order Cancelled
            format_s = "!cQIIc"
        else:
            raise Exception(f"Unsupported message type '{header}'")
        package = tuple(package) 

        return struct.pack(format_s, *package)

    @staticmethod
    def unpackage(header: bytes, body: bytes) -> dict:
        """
        Parse bytes input from the TCP socket into a dictionary output.

        :param header: First byte of an inbound message denoting the order type.
        :param body: Rest of the bytes of an inbound message.
        :returns: Dictionary with fields formatted according to the OUCH protocol.
        :raises Exception: Header is an invalid byte.
        """
        
        message_dict = None 
        if header == b'O': # Place Order
            message_dict = Util._unpackage_enter_order(body)
        elif header == b'U':
            if len(body) == 25: # Replace Order
                message_dict = Util._unpackage_replace_order(body)
            elif len(body) == 51: # Order Replaced
                message_dict = Util._unpackage_replace_message(body)
            else:
                raise Exception(f"Unsupported replace order length {len(body)}")
        elif header == b'X': # Cancel Order
            message_dict = Util._unpackage_cancel_order(body)
        elif header == b'S': # System Event
            message_dict = Util._unpackage_system_message(body)
        elif header == b'J': # Order Rejected
            message_dict = Util._unpackage_order_rejected(body)
        elif header == b'A': # Order Accepted
            message_dict = Util._unpackage_order_accepted(body)
        elif header == b'C': # Order Cancelled
            message_dict = Util._unpackage_order_cancelled(body)
        else:
            raise Exception(f"Unsupported message type '{header}'")

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
        format_s = "!I10scII4sIIIccIcc"
        msg_dict = Util._unpackage(names, body, format_s, 'O')
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
        msg_dict = Util._unpackage(names, body, format_s, 'U')
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
        msg_dict = Util._unpackage(names, body, format_s, 'X')
        return msg_dict

    @staticmethod
    def _unpackage_replace_message(body: bytes):
        names = (
            "message_type",
            "timestamp",
            "replacement_order_token",
            "buy_sell_indicator",
            "quantity",
            "orderbook_id",
            "group",
            "price",
            "time_in_force",
            "display",
            "order_number",
            "minimum_quantity",
            "order_state",
            "previous_order_token"
        )
        format_s = "!QIcII4sIIcQIcI"
        msg_dict = Util._unpackage(names, body, format_s, 'U')
        return msg_dict
    
    @staticmethod
    def _unpackage_system_message(body: bytes):
        names = (
            "message_type",
            "timestamp",
            "system_event"
        )
        format_s = "!Qc"
        msg_dict = Util._unpackage(names, body, format_s, 'S')
        return msg_dict

    @staticmethod
    def _unpackage_order_rejected(body: bytes):
        names = (
            "message_type",
            "timestamp",
            "order_token",
            "order_rejected_reason"
        )
        format_s = "!QIc"
        msg_dict = Util._unpackage(names, body, format_s, 'J')
        return msg_dict
    
    @staticmethod
    def _unpackage_order_accepted(body: bytes):
        names = (
            "message_type",
            "timestamp",
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
            "order_number",
            "minimum_quantity",
            "order_state",
            "order_classification",
            "cash_margin_type"
        )
        format_s = "!QI10scII4sIIIccQIccc"
        msg_dict = Util._unpackage(names, body, format_s, 'A')
        return msg_dict

    @staticmethod
    def _unpackage_order_cancelled(body: bytes):
        names = (
            "message_type",
            "timestamp",
            "order_token",
            "decrement_quantity",
            "order_cancelled_reason"
        )
        format_s = "!QIIc"
        msg_dict = Util._unpackage(names, body, format_s, 'C')
        return msg_dict

    @staticmethod
    def _unpackage(names: tuple, body: bytes, format_s: str, prefix=None):
        """General method for unpackaging orders"""
        fields = struct.unpack(format_s, body)

        if prefix != None and isinstance(prefix, str):
            fields = (prefix, ) + fields
        msg_dict = dict(zip(names, fields))

        if "price" in msg_dict.keys():
            msg_dict["price"] = msg_dict["price"]/10

        for key in msg_dict.keys():
            if isinstance(msg_dict[key], bytes):
                msg_dict[key] = msg_dict[key].decode("ascii").strip()
            if msg_dict[key] == "":
                msg_dict[key] = " "
        
        return msg_dict
    
    @staticmethod
    def unsigned_int(n: int):
        return n % 2**32 if n >= 0 else n + 2**32

    @staticmethod
    def get_addr() -> int:
        """Get socket address defined in the config file."""
        config = configparser.ConfigParser()
        config.read("config.ini")
        host = config['DEFAULT']['host']
        port = int(config['DEFAULT']['port'])
        return host, port