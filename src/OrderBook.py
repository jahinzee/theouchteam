import time


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

        return success, outbound

    def test(self):
        testing = [[{
            'message_type': 'O',
            'order_token': 0,
            'indicator': 'B',
            'quantity': 200,
            'price': 323.4,
            'time_in_force': 100,
            'display': "h"
        },0], [{
            'message_type': 'U',
            'existing_order_token': 0,
            'replacement_order_token': 1,
            'quantity': 5000,
            'price': 323.4,
            'time_in_force': 100
        }, 1], [{
            'message_type': 'O',
            'order_token': 1,
            'indicator': 'B',
            'quantity': 300,
            'price': 323.4,
            'time_in_force': 100,
            'display': "h"
        },0], [{
            'message_type': 'U',
            'existing_order_token': 0,
            'replacement_order_token': 2,
            'quantity': 5000,
            'price': 323.4,
            'time_in_force': 100
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

            # message_type = res['message_type']
            #
            # if message_type == "O":
            #     order_message = self.parse_order_message(res)
            #     self.handle_enter(res)
            #
            #
            # elif message_type == "U":
            #     replace_message = self.parse_replace_message(res)
            #     self.handle_replace(res)
            #
            # elif message_type == "X":
            #     cancel_message = self.parse_cancel_message(res)
            #     self.handle_cancel(res)
            #
            # else:
            #     print("message type error")
            #
            # print(self.order_book)
            # print(self.token_valid)
            # print("next")

    def input_order(self, indicator, quantity, price, time_in_force, time_received, order_id, order_token):
        if price not in self.order_book:
            self.order_book[price] = [[indicator, price, quantity, time_in_force, time_received, order_id, order_token]]
        else:
            # if price is already in order book
            self.order_book[price].append([indicator, price, quantity, time_in_force, time_received, order_id, order_token])

    def get_message_type(self, res):
        return {}

    def parse_order_message(self, res):
        return {}

    def parse_replace_message(self, res):
        return {}

    def parse_cancel_message(self, res):
        return {}

    def check_order_valid(self, order_message):

        #Rayman's code
        # success = True
        # err_code = ""
        #
        # if content["orderbook_id"] > 9999:
        #     err_code = "S"
        #
        # elif content["price"] > self.PRICE_MAX:
        #     err_code = "X"
        #
        # elif content["quantity"] > self.QUANTITY_MAX:
        #     err_code = "Z"
        #
        # elif content["minimum_quantity"] > 0 and content["time_in_force"] == 0:
        #     err_code = "N"
        #
        # elif content["buy_sell_indicator"] not in ("B", "S", "T", "E") or \
        #         content["order_classicification"] not in ("1", "3", "4", "5", "6") or \
        #         content["time_in_force"] not in (0, 99999):
        #     err_code = "Y"
        #
        # elif content["display"] not in ("P", ""):
        #     err_code = "D"
        #
        # elif content["cash_margin_type"] not in ("1", "2", "3", "4", "5"):
        #     err_code = "G"

        # checks whether invalid quantity:
        success = True
        rejected_reasons = ""

        if order_message['quantity'] == 0:

            rejected_reasons = "Z"

            success = False

        # check whether invalid display
        elif order_message['display'] == "":
            rejected_reasons = "D"
            success = False

        # check whether invalid order price
        elif order_message['price'] <= 0:
            rejected_reasons = "X"
            success = False

        elif order_message['indicator'] != 'B' and order_message['indicator'] != 'S':
            rejected_reasons = "Y"
            success = False

        return success, rejected_reasons

    def handle_enter(self, order_message, client_id, order_id):
        # to check if successful
        order_token = order_message['order_token']

        indicator = order_message['indicator']

        quantity = order_message['quantity']

        price = order_message['price']

        time_in_force = order_message['time_in_force']

        time_received = time.time()

        if client_id not in self.curr_order_token:
            #check whether you have to initialise curr_order_token for that specific client
            self.curr_order_token[client_id] = -1

        if client_id not in self.token_valid:
            self.token_valid[client_id] = []

        # check whether order_token is not valid
        if order_token != self.curr_order_token[client_id] + 1:
            # Out of sequence token
            # Token out of sequence will be silently ignored
            success = False
            outbound = "invalid order token"

        else:

            #check whether the order information is valid
            success, rejected_reasons = self.check_order_valid(order_message)

            if success:
                self.input_order(indicator, quantity, price, time_in_force, time_received, order_id, order_token)

                # calls function to output a successful response
                outbound = self.output_accepted(order_message)

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
        time_received = time.time()

        if client_id in self.curr_order_token and existing_order_token >= 0 and existing_order_token <= self.curr_order_token[client_id] and replacement_order_token == self.curr_order_token[client_id] + 1 and \
                self.token_valid[client_id][existing_order_token] == True:

            for order_level in self.order_book.values():
                for i, order in enumerate(order_level):
                    # loop through each order to find matching order_token and check whether client is matching
                    if order[-1] == existing_order_token and order[-2] == hash(str(client_id) + str(existing_order_token)):
                        #nb reason why i didn't use the self.get_order_id function is becasue that function takes replacement_order_token, but we are checking existing


                        indicator = order[0]
                        order_level.pop(i)  # remove original from order book

            # increase the current order token number to match new order token number
            self.curr_order_token[client_id] += 1

            self.token_valid[client_id].append(True)
            self.token_valid[client_id][existing_order_token] = False

            if price not in self.order_book:
                self.order_book[price] = [
                    [indicator, price, quantity, time_in_force, time_received, order_id, replacement_order_token]]
            else:
                # if price is already in order book
                self.order_book[price].append(
                    [indicator, price, quantity, time_in_force, time_received, order_id, replacement_order_token])

            outbound = self.output_replaced(replace_message)

            success = True

        else:
            # if not valid order_token and/or replacement_order_token
            success = False

            outbound = {} # <----- not sure if this is appropriate. Can't find correct response for invalid replace

        return success, outbound

    def handle_cancel(self, cancel_message, client_id, order_id):
        order_token = cancel_message['order_token']
        if client_id in self.token_valid and self.token_valid[client_id][order_token]:
            # i.e. if specific order has not been cancelled or replaced
            for order_level in self.order_book.values():
                for i, order in enumerate(order_level):
                    # loop through each order to find matching order_token
                    if order[-1] == order_token and order[-2] == order_id:
                        quantity = order[2]
                        order_level.pop(i)  # remove original from order book
                        self.token_valid[client_id][order_token] = False

            outbound = self.output_cancelled(cancel_message, 'U', quantity)
            success = True
        else:
            outbound = self.output_cancelled(cancel_message, 'U', 0)
            success = False

        return success, outbound

    def output_accepted(self, order_message):
        # An Order Accepted Message acknowledges the receipt and acceptance of a valid Enter Order Message

        #to keep standard with all other functions
        msg = order_message

        #print(msg)

        return msg

    def output_cancelled(self, cancel_message, cancelled_reason, quantity):
        # An Order Canceled Message informs that an order has been canceled. This could be acknowledging a Cancel Order Message, or it could be the result of the order being canceled automatically.

        msg = {
            'message_type': "C",
            'timestamp': time.time(),
            'order_token': cancel_message['order_token'],
            'decrement quantity': quantity,
            'order_cancelled_reason': cancelled_reason
        }

        #print(msg)

        return msg

    def output_replaced(self, replace_message):
        # An Order Replaced Message acknowledges the receipt and acceptance of a valid Replace Order Message
        # The data fields from the Replace Order Message are echoed back in this message

        # to keep standard with all other functions
        msg = replace_message

        #print(msg)

        return msg

    def output_executed(self):
        # An Order Executed Message informs that all or part of an order has been executed
        pass

    def output_rejected(self, order_message, rejected_reasons):
        # An Order Rejected Message may be sent in response to an Enter Order Message if the order cannot be accepted.
        msg = {
            'message_type': 'J',
            'timestamp': time.time(),
            'order_token': order_message['order_token'],
            'order_rejected_reason': rejected_reasons
        }

        #print(msg)

        return msg


if __name__ == "__main__":
    a = OrderBook()
    a.test()
