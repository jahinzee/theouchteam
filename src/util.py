import struct
import datetime


class Util():

    """
    get_server_time

    returns nanoseconds elasped since midnight - 0 nanoseconds as datetime only has microsecond accuracy.
    the time module has no way of returning the timestamp of midnight.
    """
    def get_server_time():
        seconds = (datetime.datetime.now() - datetime.combine(datetime.date.today(), datetime.min.time())).total_seconds() 
        return seconds / (datetime.timedelta(microseconds=1)*1000)

    """
    package_outbound
    package is list of fields
    """
    @staticmethod
    def package_outbound(package):
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
        return struct.pack(format_s, *package)

    """
    pack_message

    Message should be a tuple with fields in the order defined in the
    Japannext OUCH Trading Specification.

    The price field should an integer, calculated using the formula price_field = int(price*10).
    Alpha fields should be a bytes object representing a string or character i.e: Use b'Python' instead of 'Python' 
    """
    @staticmethod
    def package_inbound(msg):
        header = msg[0]
        format_s = None
        if header == b'O':
            format_s = "!cI10scIi4siIIccIcc"
        elif header == b'U':
            format_s = "!cIIIiIcI"
        elif header == b'X':
            format_s = "!cII"
        else:
            raise Exception(f"Invalid header '{header}'")
        
        return struct.pack(format_s, *msg)