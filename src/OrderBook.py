from util import Util

class OrderBook:
    PRICE_MAX = 214748364.6
    QUANTITY_MAX = 2147483647

    def __init__(self):
        self.order_book = {}  # limit order book
        self.curr_order_token = {}  # current order token number
        self.token_valid = {}  # boolean array to check whether token is still valid in the scenario you trying to replace an order thats already been replaced
        self.rejected_reasons_list = {
            'H': "There is currently a trading halt so no orders can be accepted on this orderbook at this time",
            'S': "Invalid orderbook identifier",
            'X': "Invalid price",
            'Z': "Invalid quantity",
            'N': "Invalid minimum quantity",
            'Y': "Invalid order type",
            'D': "Invalid display type",
            'V': "Exceeded order value limit",
            'i': "Short sell order restriction",
            'R': "Order not allowed at this time",
            'F': "Flow control is enabled and this OUCH port is being throttled",
            'G': "Invalid margin specification",
            'L': "MPID not allowed for this port",
            'c': "User does not have permission to enter an order on the given board",
            'O': "Other"
        }

    def get_order_id(self, client_id, order_message):
        if 'message_type' not in order_message:
            return None
        elif order_message['message_type'] == 'O':
            return hash(str(client_id) + str(order_message['order_token']))
        elif order_message['message_type'] == 'U':
            return hash(str(client_id) + str(order_message['replacement_order_token']))
        elif order_message['message_type'] == 'X':
            return hash(str(client_id) + str(order_message['order_token']))
        else:
            return None

    def get_book(self):
        return self.order_book

    def input_order(self, buy_sell_indicator, quantity, orderbook_id, price, time_in_force, time_received, order_id, order_token):
        if price not in self.order_book:
            self.order_book[price] = [[buy_sell_indicator, price, quantity, orderbook_id, time_in_force, time_received, order_id, order_token]]
        else:
            # if price is already in order book
            self.order_book[price].append([buy_sell_indicator, price, quantity, orderbook_id, time_in_force, time_received, order_id, order_token])

    def check_enter_valid(self, order_message, client_id, order_token):

        success = False
        err_code = ""

        # check whether order_token is not valid
        if order_token <= self.curr_order_token[client_id]:
            # Out of sequence token
            # Token out of sequence will be silently ignored
            err = "O"
        elif order_message["orderbook_id"] > 9999 or order_message["orderbook_id"] < 0:
            err_code = "S"
        elif order_message["price"] > self.PRICE_MAX or order_message["price"] <= 0:
            err_code = "X"
        elif order_message["quantity"] > self.QUANTITY_MAX or order_message["quantity"] <= 0:
            err_code = "Z"
        elif order_message["minimum_quantity"] > 0 and order_message["time_in_force"] == 0:
            err_code = "N"
        elif order_message["buy_sell_indicator"] not in ("B", "S", "T", "E") or order_message["order_classification"] not in ("1","2","3","4","5","6"):
            err_code = "Y"
        elif order_message["display"] not in ("P", ""):
            err_code = "D"
        elif order_message["cash_margin_type"] not in ("1","2","3","4","5"):
            err_code = "G"
        else:
            success = True

        return success, err_code

    def check_replace_valid(self, order_message):
        success = False
        err_code = ""

        if order_message["price"] > self.PRICE_MAX or order_message["price"] <= 0:
            err_code = "X"
        elif order_message["quantity"] > self.QUANTITY_MAX or order_message["quantity"] <= 0:
            err_code = "Z"
        elif order_message["minimum_quantity"] > 0 and order_message["time_in_force"] == 0:
            err_code = "N"
        elif order_message["display"] not in ("P", ""):
            err_code = "D"
        else:
            success = True

        return success, err_code

    def handle_order(self, client_id: int, res: dict) -> (bool, dict):
        """
        This is the handler function to handle all incoming streams (res)
        It returns the outbound message required to send back to client and whether order was successful
        """
        success, outbound = None, None
        message_type = res['message_type']
        order_id = self.get_order_id(client_id, res)

        if message_type == "O":
            success, outbound = self.handle_enter(res, client_id, order_id)
        elif message_type == "U":
            success, outbound = self.handle_replace(res, client_id, order_id)
        elif message_type == "X":
            success, outbound = self.handle_cancel(res, client_id, order_id)
        else:
            print("message type error")
            raise ValueError(f"message type {message_type} is not supported")

        return success, outbound

    def handle_enter(self, order_message, client_id, order_id):
        # to check if successful
        order_token = order_message['order_token']
        buy_sell_indicator = order_message['buy_sell_indicator']
        orderbook_id = order_message['orderbook_id']
        quantity = order_message['quantity']
        price = order_message['price']
        time_in_force = order_message['time_in_force']
        time_received = Util.get_server_time()

        if client_id not in self.curr_order_token:
            # check whether you have to initialise curr_order_token for that specific client
            self.curr_order_token[client_id] = -1

        if client_id not in self.token_valid:
            self.token_valid[client_id] = []


        #check whether the order information is valid
        success, rejected_reasons = self.check_enter_valid(order_message, client_id, order_token)

        if success:
            self.input_order(buy_sell_indicator, quantity, orderbook_id, price, time_in_force, time_received, order_id, order_token)

            # Order is always live as there is no matching engine.

            order_state = "L"
            # calls function to output a successful response
            outbound = self.output_accepted(order_message, order_id, order_state)

            # increase the current order token number to match
            self.curr_order_token[client_id] += 1

            self.token_valid[client_id].append(True)
        else:
            # if invalid
            outbound = self.output_rejected(order_message, rejected_reasons)

        return success, outbound

    def handle_replace(self, replace_message, client_id, order_id):
        existing_order_token = replace_message['existing_order_token']
        replacement_order_token = replace_message['replacement_order_token']
        quantity = replace_message['quantity']
        price = replace_message['price']
        time_in_force = replace_message['time_in_force']
        time_received = Util.get_server_time()

        if client_id in self.curr_order_token \
                and existing_order_token >= 0 \
                and existing_order_token <= self.curr_order_token[client_id] \
                and replacement_order_token == self.curr_order_token[client_id] + 1 \
                and self.token_valid[client_id][existing_order_token] == True:
            checkValid = False

            for order_level in self.order_book.values():
                for i, order in enumerate(order_level):
                    # loop through each order to find matching order_token and check whether client is matching
                    if order[-1] == existing_order_token and order[-2] == hash(str(client_id) + str(existing_order_token)):
                        #nb reason why i didn't use the self.get_order_id function is becasue that function takes replacement_order_token, but we are checking existing
                        checkValid = True
                        buy_sell_indicator = order[0]
                        orderbook_id = order[3]
                        order_level.pop(i)  # remove original from order book


            success, rejected_reasons = self.check_replace_valid(replace_message)

            if checkValid == False:
                #i.e. happens in very rare scenarios where tokens match up but different client_id
                print("!!!")
                success = False
                outbound = output_rejected(replace_message, "O")
            elif success == False:
                outbound = output_rejected(replace_message, "rejected_reasons")
            else:
                # increase the current order token number to match new order token number
                self.curr_order_token[client_id] += 1
                order_state = "L"

                self.token_valid[client_id].append(True)
                self.token_valid[client_id][existing_order_token] = False

                if price not in self.order_book:
                    self.order_book[price] = [
                        [
                            buy_sell_indicator, 
                            price, 
                            quantity, 
                            orderbook_id, 
                            time_in_force, 
                            time_received, 
                            order_id, 
                            replacement_order_token
                        ]
                    ]
                else:
                    # if price is already in order book
                    self.order_book[price].append(
                        [
                            buy_sell_indicator, 
                            price, 
                            quantity, 
                            orderbook_id, 
                            time_in_force, 
                            time_received,
                            order_id, 
                            replacement_order_token
                        ]
                    )
                outbound = self.output_replaced(replace_message, order_id, order_state)
                success = True
        else:
            # if not valid order_token and/or replacement_order_token
            success = False
            outbound = [] # <----- not sure if this is appropriate. Can't find correct response for invalid replace

        return success, outbound

    def handle_cancel(self, cancel_message, client_id, order_id):
        order_token = cancel_message['order_token']

        if client_id in self.token_valid and self.token_valid[client_id][order_token]:
            # i.e. if specific order has not been cancelled or replaced
            for order_level in self.order_book.values():
                for i, order in enumerate(order_level):
                    # loop through each order to find matching order_token
                    if order[-1] == order_token \
                            and order[-2] == order_id  \
                            and order[-2] == self.get_order_id(client_id, cancel_message):
                        quantity = order[2]
                        order_level.pop(i)  # remove original from order book
                        self.token_valid[client_id][order_token] = False

            outbound = self.output_cancelled(cancel_message, 'U', quantity)
            success = True
        else:
            outbound = self.output_cancelled(cancel_message, 'U', 0)
            success = False

        return success, outbound

    def output_accepted(self, order_message, order_id, order_state):
        # An Order Accepted Message acknowledges the receipt and acceptance of a valid Enter Order Message
        #to keep standard with all other functions
        msg = list(order_message.values())
        msg.insert(1, Util.get_server_time())
        msg.insert(13, order_id)
        msg.insert(15, order_state)

        return msg

    def output_cancelled(self, cancel_message, cancelled_reason, quantity):
        # An Order Canceled Message informs that an order has been canceled. This could be acknowledging a 
        # Cancel Order Message, or it could be the result of the order being canceled automatically.
        msg = [
            "C",
            Util.get_server_time(),
            cancel_message['order_token'],
            quantity,
            cancelled_reason
        ]
        return msg

    def output_replaced(self, replace_message, order_id, order_state):
        # An Order Replaced Message acknowledges the receipt and acceptance of a valid Replace Order Message
        # The data fields from the Replace Order Message are echoed back in this message
        # to keep standard with all other functions
        msg = list(replace_message.values())
        msg.append(msg[1])
        msg[1] = Util.get_server_time()
        msg.insert(10, order_id)
        msg.insert(12, order_state)
        return msg

    def output_executed(self):
        # An Order Executed Message informs that all or part of an order has been executed
        pass

    def output_rejected(self, order_message, rejected_reasons):
        # An Order Rejected Message may be sent in response to an Enter Order Message if the order cannot be accepted.
        msg = [
            'J',
            Util.get_server_time(),
            order_message['order_token'],
            rejected_reasons
        ]
        return msg

    def test(self):
        # testing = [[{
        #     'message_type': 'O',
        #     'order_token': 0,
        #     'buy_sell_indicator': 'B',
        #     'quantity': 200,
        #     'orderbook_id': 3,
        #     'price': 323.4,
        #     'time_in_force': 100,
        #     'display': "h"
        # },0], [{
        #     'message_type': 'U',
        #     'existing_order_token': 0,
        #     'replacement_order_token': 1,
        #     'quantity': 5000,
        #     'orderbook_id': 3,
        #     'price': 323.4,
        #     'time_in_force': 100
        # }, 0], [{
        #     'message_type': 'O',
        #     'order_token': 2,
        #     'buy_sell_indicator': 'B',
        #     'quantity': 300,
        #     'orderbook_id': 3,
        #     'price': 325.4,
        #     'time_in_force': 100,
        #     'display': "h"
        # },0],  [{
        #     'message_type': 'O',
        #     'order_token': 2,
        #     'buy_sell_indicator': 'B',
        #     'quantity': 500,
        #     'orderbook_id': 3,
        #     'price': 327.4,
        #     'time_in_force': 100,
        #     'display': "h"
        # },1],
        #     [{
        #     'message_type': 'U',
        #     'existing_order_token': 1,
        #     'replacement_order_token': 3,
        #     'quantity': 5000,
        #     'orderbook_id': 3,
        #     'price': 323.4,
        #     'time_in_force': 100
        # }, 0],[{
        #     'message_type': 'X',
        #     'order_token': 2,
        #     'quantity': None
        # },0],
        #
        # ]

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
        },0],  [{
            'message_type': 'U',
            'existing_order_token': 0,
            'replacement_order_token': 1,
            'quantity': 5000,
            'price': 323.4,
            'time_in_force': 100,
            'display': 'P',
            'minimum_quantity': 23
        }, 0]
        ]

        for res in testing:
            success, outbound = self.handle_order(res[1], res[0])
            print("--------")
            print(res[1])
            print(success, outbound)
            print(self.order_book)
            print(self.token_valid)
            print("--------")


if __name__ == "__main__":
    a = OrderBook()
    a.test()