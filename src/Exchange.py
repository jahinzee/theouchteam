"""
The Ouch Team
Exchange Integration

Integration of all required classes together into a working implementation. Will be changed
as new components are added. This is mostly for knowing what we have to implement in future modules.
"""
import threading
import time
import json

from OrderBook import OrderBook
from parse_inbound import pack_message, parse
from tcpip.receiver import receiver
from util import Util

class Exchange():
    PRICE_MAX = 214748364.6
    QUANTITY_MAX = 2147483647 

    def __init__(self):
        # Exchange state variables
        self.open = False
        # Connection receiver
        self.connection_manager = receiver()
        self.msg_queue = self.connection_manager.get_queue()

        # Orderbook
        self.orderbook = OrderBook()
        self.client_tokens = {}

        # Outputting orderbook once per second, change to silent-mode later.
        self.printer = threading.Thread("printer", lambda: self.print_orderbook_thread(), daemon=True)

        self.operation_thread = threading.Thread("operate", lambda: self.operate(), daemon=True)
        input() # Let main thread run
    
    def print_orderbook_thread(self):
        while True:
            time.sleep(1)
            print(json.dumps(
                self.orderbook.get_book(),
                indent = 4,
                separators = (',', ': ')
            ))
    
    def operate(self):
        while True:
            msg = self.msg_queue.get()
            if msg["type"] == "C":
                if self.closed:
                    outbound = ["S", Util.get_server_time(), "S"]
                else:
                    outbound = ["S", Util.get_server_time(), "E"]
                self.connection_manager.send_message(msg["id"], Util.package_outbound(outbound))
            else:
                client_id = msg["id"]
                content = parse(msg["header"], msg["body"])
                if client_id not in self.client_tokens.keys():
                    self.client_tokens[client_id] = 0 # Assume that client tokens increment from 1
                valid = self.validate_order(content, client_id)

                msg_type = content["message_type"]
                if not valid:
                    if msg_type == 'U':
                        # Section 6.3
                        msg_type == "X"
                        content = {
                            "message_type": "X",
                            "order_token": content["existing_order_token"],
                            "quantity": content["quantity"]
                        }
                    else:
                        return
                
                success, orderbook_msg = self.orderbook.handle_order(client_id, content)
                if msg_type == 'U' and success:
                    self.client_tokens[client_id] = content["replacement_order_token"]
                self.connection_manager.send_message(client_id, Util.package_outbound(orderbook_msg))
                

    def validate_order(self, content, client_id):
        msg_type = content["message_type"]
        err_code = None
        if msg_type == 'O':
            if content["order_token"] <= self.client_tokens[client_id]:
                return False
            elif content["order_id"] > 9999:
                err_code = "S"
            elif content["price"] > self.PRICE_MAX:
                err_code = "X"
            elif content["quantity"] > self.QUANTITY_MAX:
                err_code = "Z"
            elif content["minimum_quantity"] > 0 and content["time_in_force"] == 0:
                err_code = "N"
            elif content["buy_sell_indicator"] not in ("B", "S", "T", "E") or \
                    content["order_classicification"] not in ("1", "3", "4", "5", "6") or \
                    content["time_in_force"] not in (0, 99999):
                err_code = "Y"
            elif content["display"] not in ("P", ""):
                err_code = "D"
            elif content["cash_margin_type"] not in ("1", "2", "3", "4", "5"):
                err_code = "G"
            else:
                return True
            outbound = ["J", Util.get_server_time(), content["order_token"], err_code]
            self.connection_manager.send_message(client_id, Util.package_outbound(outbound))
            return False
        elif msg_type == 'U':
            if content["replacement_order_token"] <= self.client_tokens[client_id]:
                return False

    def handle_signal(self):
        # implement with sigill in windows and sigusr1 in linux
        # use sys.platform to check operating system
        pass 

    def open_exchange(self):
        self.open = True
    
    def close_exchange(self):
        self.open = False