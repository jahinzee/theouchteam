"""
The Ouch Team
Exchange Integration

Integration of all required classes together into a working implementation. Will be changed
as new components are added. This is mostly for knowing what we have to implement in future modules.
"""
import threading
import time
import json

from orderbook import OrderBook
from receiver import Receiver
from util import Util
from console import Console


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
        self.open = True

        # Connection receiver
        self.connection_manager = Receiver()
        self.msg_queue = self.connection_manager.get_queue()

        # Orderbook
        self.orderbook = OrderBook()

        # Outputting orderbook once per second, change to silent-mode later.
        self.print_dict = threading.Event()
        self.printer = threading.Thread(name="printer", target=lambda: self._print_orderbook_thread(), daemon=True)
        self.printer.start()

        self.operation_thread = threading.Thread(name="operate", target=lambda: self._operate(), daemon=True)
        self.operation_thread.start()

    def open_exchange(self):
        """Open the exchange and allow clients to place orders."""
        self.open = True
    
    def close_exchange(self):
        """Close the exchange and prevent clients from place orders."""
        self.open = False
    
    def print_orderbook(self):
        """Prints the Orderbook to the console in a nice format."""
        Console(loadfrom=self.orderbook.get_book()).print()
        """
        self.print_dict.clear()
        self.orderbook.debug()
        self.print_dict.wait()
        """
    
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
                if not self.open:
                    outbound = ["S", Util.get_server_time(), "S"]
                else:
                    outbound = ["S", Util.get_server_time(), "E"]
                self.connection_manager.send_message(msg["id"], Util.package(outbound))
            else:
                # Parse message if it's not a connection.
                client_id = msg["id"]
                content = Util.unpackage(msg["header"], msg["body"])

                # Validate order fields according to the OUCH protocol.
                valid, outbound = self._validate_order_syntax(content, client_id)

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
                        valid = True
                
                # Pass valid order into the orderbook
                if valid:
                    success, outbound = self.orderbook.handle_order(client_id, content)

                if len(outbound) == 0: 
                    self.print_dict.set()
                    continue

                # Send outbound message back to client.
                self.connection_manager.send_message(client_id, Util.package(outbound))
            self.print_dict.set()
                

    def _validate_order_syntax(self, content: dict, client_id: int) -> (bool, list):
        """
        Validates the formatting of the order from a specfic client.

        :param content: Decoded and parsed messaged sent by the client.
        :param client_id: Unique Integer ID assigned to each client by the receiver.
        :returns: boolean of whether the order is allowed or not.
        """
        msg_type = content["message_type"]
        err_code = None
        outbound = []
        if msg_type == 'O':
            # Checking Error rejected reasons in Table 3 Section 7.7.
            # Not Implemented: H, V, i, R, F, L, C, O
            if content["orderbook_id"] > 3 or content["orderbook_id"] < 0:
                err_code = "S"
            elif content["price"] > self.PRICE_MAX:
                err_code = "X"
            elif content["quantity"] > self.QUANTITY_MAX:
                err_code = "Z"
            elif content["minimum_quantity"] > 0 and content["time_in_force"] != 0:
                err_code = "N"
            elif content["buy_sell_indicator"] not in ("B", "S", "T", "E") or \
                    content["order_classification"] not in ("1", "3", "4", "5", "6") or \
                    content["time_in_force"] not in (0, 99999):
                err_code = "Y"
            elif content["display"] not in ("P", " "):
                err_code = "D"
            elif content["cash_margin_type"] not in ("1", "2", "3", "4", "5"):
                err_code = "G"
            else:
                return True, outbound
            outbound = ["J", Util.get_server_time(), content["order_token"], err_code]
            return False, outbound
        elif msg_type == 'U':
            if content["price"] > self.PRICE_MAX:
                err_code = "X"
            elif content["quantity"] > self.QUANTITY_MAX:
                err_code = "Z"
            elif content["minimum_quantity"] > 0 and content["time_in_force"] != 0:
                err_code = "N"
            elif content["time_in_force"] not in (0, 99999):
                err_code = "Y"
            elif content["display"] not in ("P", " "):
                err_code = "D"
            else:
                return True, outbound
            return False, outbound
        elif msg_type == 'X':
            return True, outbound
        else:
            raise ValueError(f"Invalid header detected in Exchange validation.")


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