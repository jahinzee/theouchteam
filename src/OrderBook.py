import time
import pprint
import copy

from src.util import Util

class OrderBook:
    PRICE_MAX = 214748364.6
    QUANTITY_MAX = 2147483647

    def __init__(self):
        # Limit order book.
        # {price: [<order>, <order>, ...]} where each order is a list
        self.order_book = {}

        # Tokens in use dict:{client_id: [int, int, ...]}
        self.tokens_used = {} 

        # Order hashmap dict:{order_id: <order>}
        self.order_hashmap = {}

        # Hashmap to support keeping order_id the same after replacement.
        # dict:{latest order_id: first order_id}
        self.order_id_aliases = {}

        # List of active order ids
        self.active_order_ids = []

        # For debugging
        self.debug_cycle = 1
    
    def debug(self):
        """Outputs all fields of the orderbook onto the console."""
        names = ("Order Book: ", "Tokens Used: ", "Order Hashmap: ", "Order ID Aliases: ")
        books = (self.order_book, self.tokens_used, self.order_hashmap, self.order_id_aliases, self.active_order_ids)
        print(f"-----------------DEBUG CYCLE {self.debug_cycle}------------------")
        for i in range(len(names)):
            print(names[i])
            pprint.pprint(books[i])
            print("")
        self.debug_cycle += 1

    def get_book(self) -> dict:
        """
        Return a deepcopy of the orderbook. A deepcopy is returned as the console output 
        implementation modifies the list referenced in the orderbook. To improve performance, 
        the output implementation must be modified to not change the orderbook. So a shallow
        copy can be used instead.
        """
        return copy.deepcopy(self.order_book)

    def handle_order(self, client_id: int, msg: dict): # -> (bool, dict):
        """Handles an incoming order from a client."""
        success, outbound = self._validate_order(client_id, msg)
        if success:
            outbound = self._process_order(client_id, msg)
        if outbound == None:
            raise Exception("Did not handle all validation or processing cases.")
        return success, outbound
    
    def _validate_order(self, client_id: int, msg: dict): # -> (bool, list):
        """Checks for order token validity."""
        order_type = msg["message_type"]
        if order_type == "O": # Validate enter order message
            success, outbound = self._validate_enter_order(client_id, msg)
        elif order_type == "U": # Validate replace order message
            success, outbound = self._validate_replace_order(client_id, msg)
        elif order_type == "X": # Validate delete order message
            success, outbound = self._validate_cancel_order(client_id, msg)
        else:
            raise ValueError(f"Invalid order type {order_type} caught in OrderBook.")
        return success, outbound
    
    def _validate_enter_order(self, client_id: int, msg: dict): # -> (bool, list):
        """
        Checks contextual validity of an enter order.
        
        :returns : whether or not the order should be accepted.
        """
        token = msg["order_token"]
        if not client_id in self.tokens_used.keys():
            self.tokens_used[client_id] = []
            return True, None
        else:
            greatest_token = self.tokens_used[client_id][-1]
            if token <= greatest_token:
                return False, []
            else:
                return True, None
    
    def _validate_replace_order(self, client_id: int, msg: dict): # -> (bool, list):
        """Checks contextual validity of a replace order."""
        exst_token = msg["existing_order_token"]
        repl_token = msg["replacement_order_token"]
        exst_order_id = self._get_order_id(client_id, exst_token)
        if not exst_order_id in self.active_order_ids:
            return False, []
        else:
            greatest_token = self.tokens_used[client_id][-1]
            if repl_token <= greatest_token:
                return False, []
            else:
                return True, None
    
    def _validate_cancel_order(self, client_id: int, msg: dict): # -> (bool, list):
        """Checks contextual validity of a cancel order."""
        order_id = self._get_order_id(client_id, msg["order_token"])
        if not order_id in self.active_order_ids:
            return False, []
        else:
            return True, None
    
    def _process_order(self, client_id: int, msg: dict) -> list:
        """
        Processes the order by using its information to modify the orderbook dictionary.
        The message should be validated before being passed into
        this function.
        """
        # Match orderbook tokens in use
        order_type = msg["message_type"]
        if order_type == "O": # Validate enter order message
            outbound = self._process_enter_order(client_id, msg)
        elif order_type == "U": # Validate replace order message
            outbound = self._process_replace_order(client_id, msg)
        elif order_type == "X": # Validate delete order message
            outbound = self._process_cancel_order(client_id, msg)
        else:
            raise ValueError(f"Invalid order type {order_type} caught in OrderBook.")
        return outbound

    def _process_enter_order(self, client_id: int, msg: dict) -> list:
        """Adds an order to the orderbook."""
        price = msg["price"]
        if not price in self.order_book.keys():
            self.order_book[price] = []

        token = msg["order_token"]
        order_id = self._get_order_id(client_id, token)
        order = self._build_order(client_id, msg)

        order_state = "D" if msg["time_in_force"] == 0 or msg["quantity"] == 0 else "L"
        # Don't add the order if the order is dead, but still maintain a reference to the order and its id
        if order_state != "D":
            self.order_book[price].append(order)
            self.active_order_ids.append(order_id)
        self.order_hashmap[order_id] = order
        self.order_id_aliases[order_id] = order_id
        self.tokens_used[client_id].append(token)

        # Remove level if empty
        if len(self.order_book[price]) == 0:
            self.order_book.pop(price)

        # Create outbound message
        msg["price"] = int(price*10)
        while len(msg["client_reference"]) < 10:
            msg["client_reference"] += " "
        while len(msg["group"]) < 4:
            msg["group"] += " "

        outbound = list(msg.values())
        outbound[0] = "A"
        outbound.insert(1, Util.get_server_time())
        outbound.insert(13, order_id)
        outbound.insert(15, order_state)
        return outbound

    def _build_order(self, client_id: int, msg: dict) -> list:
        """Create an order from an enter order message as a list."""
        token = msg["order_token"]
        order = [
            msg["buy_sell_indicator"],
            msg["price"],
            msg["quantity"],
            msg["orderbook_id"],
            msg["time_in_force"],
            Util.get_server_time(),
            self._get_order_id(client_id,token),
            token
        ]
        return order

    def _process_replace_order(self, client_id: int, msg: dict) -> list:
        """Replace a live order in the orderbook."""
        # Find the original order id if the order has been replaced before
        exst_token = msg["existing_order_token"]
        repl_token = msg["replacement_order_token"]
        exst_order_id = self._get_order_id(client_id, exst_token)
        repl_order_id = self._get_order_id(client_id, repl_token)

        # Update the order id alias
        orig_order_id = self.order_id_aliases.pop(exst_order_id)
        self.order_id_aliases[repl_order_id] = orig_order_id
        self.active_order_ids.remove(exst_order_id)
        self.active_order_ids.append(repl_order_id)

        # Replace order fields with replacement values.
        price = msg["price"]
        order = self.order_hashmap[orig_order_id]
        old_price = order[1]
        order[1] = price
        order[2] = msg["quantity"]
        order[4] = msg["time_in_force"]
        order[5] = Util.get_server_time()
        order[7] = repl_token

        # Remove the order if the replacement values cause it to become dead.
        self.order_book[old_price].remove(order)
        order_state = "D" if order[2] == 0 else "L"
        if order_state == "D":
            self.active_order_ids.remove(repl_order_id)
        else:
            # Create new price level if price is new
            if not price in self.order_book.keys():
                self.order_book[price] = [order]
            else:
                self.order_book[price].append(order)

        self.tokens_used[client_id].append(repl_token)

        # Remove level if empty
        if len(self.order_book[old_price]) == 0:
            self.order_book.pop(old_price)

        # Create outbound message
        msg["price"] = int(price*10)
        outbound = [
            "U",
            Util.get_server_time(),
            repl_token,
            order[0], # Buy/Sell Indicator
            order[2], # Quantity,
            order[3], # Orderbook ID
            "DAY ", # Group - Not implemented
            msg["price"],
            order[4], # Time in Force
            msg["display"],
            orig_order_id, # Order Number
            msg["minimum_quantity"], # Minimum Quantity
            order_state,
            exst_token
        ]
        return outbound

    def _process_cancel_order(self, client_id: int, msg: dict) -> list:
        """Cancels a live order in the orderbook."""
        token = msg["order_token"]
        curr_order_id = self._get_order_id(client_id, token) 
        orig_order_id = self.order_id_aliases[curr_order_id]
        order = self.order_hashmap[orig_order_id]
        price = order[1]

        self.order_book[price].remove(order)
        self.active_order_ids.remove(curr_order_id)
        if len(self.order_book[price]) == 0:
            self.order_book.pop(price)

        # Create outbound message
        outbound = [
            "C",
            Util.get_server_time(),
            token,
            order[2], # Quantity,
            "U"
        ]
        return outbound

    def _get_order_id(self, client_id: int, order_token: int):
        """
        Returns the order_id of the requested order based on the client's id and 
        passed order token. The result will always be an unsigned 32 bit integer.
        """
        return abs(hash((client_id, order_token))) % 2**32