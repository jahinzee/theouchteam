from util import Util
import json
import time
import pprint

class OrderBook:
    PRICE_MAX = 214748364.6
    QUANTITY_MAX = 2147483647

    def __init__(self):
        # Limit order book
        self.order_book = {}

        # Tokens in use dict:{client_id: [int, int, ...]}
        self.tokens_used = {} 

        # Order hashmap dict:{order_id: [<order fields>]}
        self.order_hashmap = {}

        # Hashmap to support keeping order_id the same after replacement.
        # dict:{latest order_id: first order_id}
        self.order_id_aliases = {}

        self.debug_cycle = 1
    
    def debug(self):
        names = ("Order Book: ", "Tokens Used: ", "Order Hashmap: ", "Order ID Aliases: ")
        books = (self.order_book, self.tokens_used, self.order_hashmap, self.order_id_aliases)
        time.sleep(1)
        print(f"-----------------DEBUG CYCLE {self.debug_cycle}------------------")
        for i in range(len(names)):
            """
            print(names[i] + ": " + json.dumps(
                books[i],
                indent=4,
                separators=(",", ": ")
            ))
            """
            print(names[i])
            pprint.pprint(books[i])
            print("")
        self.debug_cycle += 1

    def get_book(self) -> dict:
        return self.order_book

    def handle_order(self, client_id: int, msg: dict): # -> (bool, dict):
        success, outbound = self._validate_order(client_id, msg)
        if success:
            outbound = self._process_order(client_id, msg)
        if outbound == None:
            print(msg)
            raise Exception("Did not handle all validation or processing cases!")
        return success, outbound
    
    def _validate_order(self, client_id: int, msg: dict): # -> (bool, list):
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
        exst_token = msg["existing_order_token"]
        repl_token = msg["replacement_order_token"]
        exst_order_id = self._get_order_id(client_id, exst_token)
        if not exst_order_id in self.order_id_aliases.keys():
            return False, []
        else:
            greatest_token = self.tokens_used[client_id][-1]
            if repl_token <= greatest_token:
                return False, []
            else:
                return True, None
    
    def _validate_cancel_order(self, client_id: int, msg: dict): # -> (bool, list):
        order_id = self._get_order_id(client_id, msg["order_token"])
        if not client_id in self.tokens_used.keys() or \
                not order_id in self.order_id_aliases.keys():
            return False, []
        else:
            return True, None
    
    def _process_order(self, client_id: int, msg: dict) -> list:
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
        price = msg["price"]
        if not price in self.order_book.keys():
            self.order_book[price] = []

        token = msg["order_token"]
        order = self._build_order(client_id, msg)
        order_state = "D" if msg["time_in_force"] == 0 else "L"
        if order_state != "D":
            self.order_book[price].append(order)

        order_id = self._get_order_id(client_id, token)
        self.order_hashmap[order_id] = order
        self.order_id_aliases[order_id] = order_id
        self.tokens_used[client_id].append(token)

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

    def _build_order(self, client_id: int, msg: dict):
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
        exst_token = msg["existing_order_token"]
        repl_token = msg["replacement_order_token"]
        exst_order_id = self._get_order_id(client_id, exst_token)
        repl_order_id = self._get_order_id(client_id, repl_token)

        orig_order_id = self.order_id_aliases.pop(exst_order_id)
        self.order_id_aliases[repl_order_id] = orig_order_id

        price = msg["price"]
        order = self.order_hashmap[orig_order_id]
        order[1] = price
        order[2] = msg["quantity"]
        order[4] = msg["time_in_force"]
        order[5] = Util.get_server_time()
        order[7] = repl_token

        order_state = "D" if order[2] == 0 else "L"
        if order_state == "D":
            self.order_book[price].remove(order)

        self.tokens_used[client_id].append(repl_token)

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
        token = msg["order_token"]
        curr_order_id = self._get_order_id(client_id, token) 
        orig_order_id = self.order_id_aliases[curr_order_id]
        order = self.order_hashmap[orig_order_id]
        price = order[1]
        self.order_book[price].remove(order)
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
        return abs(hash((client_id, order_token))) % 2**32

    def test(self):
        testing = [[{
            'message_type': 'O',
            'order_token': 0,
            'client_reference': 'abcdefghij',
            'buy_sell_indicator': 'B',
            'quantity': 200,
            'orderbook_id': 3,
            'group': "DAY",
            'price': 323.4,
            'time_in_force': 100,
            'firm_id': '3434',
            'display': "P",
            'capacity': 'A',
            'minimum_quantity': 5,
            'order_classification': '1',
            'cash_margin_type': '3'
        }, 0], [{
            'message_type': 'U',
            'existing_order_token': 0,
            'replacement_order_token': 2,
            'quantity': 5000,
            'price': 323.4,
            'time_in_force': 100,
            'display': 'P',
            'minimum_quantity': 23
        }, 0], [{
            'message_type': 'X',
            'order_token': 2,
            'quantity': -10
        }, 1], [{
            'message_type': 'O',
            'order_token': 3,
            'client_reference': 'abcdefghij',
            'buy_sell_indicator': 'B',
            'quantity': 200,
            'orderbook_id': 3,
            'group': "DAY",
            'price': 323.4,
            'time_in_force': 100,
            'firm_id': '3434',
            'display': "P",
            'capacity': 'A',
            'minimum_quantity': 5,
            'order_classification': '1',
            'cash_margin_type': '3'
        }, 0]
        ]

        for res in testing:
            success, outbound = self.handle_order(res[1], res[0])
            print("--------")
            print( outbound)
            print("--------")


