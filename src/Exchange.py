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
from tcpip.receiver import receiver
from util import Util


class Exchange():
    PRICE_MAX = 214748364.6
    QUANTITY_MAX = 2147483647 

    def __init__(self):
        """
        An instance of this class should be initialised before trying to establish a connection using client.py.
        All program components are integrated together with this class, connecting the 
        receiver, orderbook, and output components. When this program is called, it will output 
        the Orderbook to the console once every second.
        """
        # Exchange state variables
        self.open = False

        # Connection receiver
        self.connection_manager = receiver()
        self.msg_queue = self.connection_manager.get_queue()

        # Orderbook
        self.orderbook = OrderBook()
        self.client_tokens = {}

        # Outputting orderbook once per second, change to silent-mode later.
        self.printer = threading.Thread(name="printer", target=lambda: self._print_orderbook_thread(), daemon=True)

        self.operation_thread = threading.Thread(name="operate", target=lambda: self._operate(), daemon=True)

    def open_exchange(self):
        """Open the exchange and allow clients to place orders."""
        self.open = True
    
    def close_exchange(self):
        """Close the exchange and prevent clients from place orders."""
        self.open = False
    
    def print_orderbook(self):
        """Prints the Orderbook to the console in a nice format."""
        print(json.dumps(
            self.orderbook.get_book(),
            indent = 4,
            separators = (',', ': ')
        ))
    
    def _operate(self):
        """
        Exchange's main function. Continuously retrieves messages from the reveiver's
        Queue, parses it into dictionary format, validates the order format, passes it to the
        OrderBook, then sends any OrderBook response back to the receiver.

        A thread of this function is automatically created upon initialisation.
        """
        while True:
            # Wait until queue has messages, then retrieve it.
            # The message is a dictionary with {"client_id": int, "header": bytes, "body": bytes}
            msg = self.msg_queue.get()

            # A new client has established a connection.
            if msg["type"] == "C":
                # Acknowledge the connection by returning a server event message.
                if self.closed:
                    outbound = ["S", Util.get_server_time(), "S"]
                else:
                    outbound = ["S", Util.get_server_time(), "E"]
                self.connection_manager.send_message(msg["id"], Util.package_outbound(outbound))
            else:
                # Parse message if it's not a connection.
                client_id = msg["id"]
                content = Util.package(msg["header"], msg["body"])
                if client_id not in self.client_tokens.keys():
                    self.client_tokens[client_id] = 0 # Assume that client tokens increment from 1

                # Validate order fields according to the OUCH protocol.
                valid = self._validate_order(content, client_id)

                msg_type = content["message_type"]
                if not valid:
                    # If a replacement order is not valid and the original order token is in use, cancel the order.
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
                
                # Pass valid order into the orderbook
                success, orderbook_msg = self.orderbook.handle_order(client_id, content)

                # Send outbound message back to client.
                if msg_type == 'U' and success:
                    self.client_tokens[client_id] = content["replacement_order_token"]
                self.connection_manager.send_message(client_id, Util.package_outbound(orderbook_msg))
                

    def _validate_order(self, content: dict, client_id: int) -> bool:
        """
        Validates the formatting of the order from a specfic client.

        :param content: Decoded and parsed messaged sent by the client.
        :param client_id: Unique Integer ID assigned to each client by the receiver.
        :returns: boolean of whether the order is allowed or not.
        """
        msg_type = content["message_type"]
        err_code = None
        # If order placement
        if msg_type == 'O':
            # Checking Error rejected reasons in Table 3 Section 7.7.
            # Not Implemented: H, V, i, R, F, L, C, O
            if content["order_token"] <= self.client_tokens[client_id]:
                return False
            elif content["order_book"] > 9999:
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

    def _handle_signal(self):
        """Handler which dumps the orderbook into a csv file when SIGUSR1 or SIGILL is caught in silent mode."""
        # implement with sigill in windows and sigusr1 in linux
        # use sys.platform to check operating system
        pass 

    def _print_orderbook_thread(self):
        """Threading wrapper for print_orderbook which outputs once every second."""
        while True:
            time.sleep(1)
            self.print_orderbook()

if __name__ == "__main__":
    Exchange()
    input()