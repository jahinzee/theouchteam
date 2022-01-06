


import time

global curr_order_token

class OrderBook:
    def __init__(self):
        self.order_book = {}  # limit order book
        self.curr_order_token = -1 # current order token number
        self.token_valid = [] # boolean array to check whether token is still valid in the scenario you trying to replace an order thats already been replaced
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

    def test(self):
        testing = [{
            'message_type': 'O',
            'order_token': 0,
            'indicator': 'B',
            'quantity': 200,
            'price': 323.4,
            'time_in_force': 100,
            'display': "h"
        }, {
            'message_type': 'U',
            'existing_order_token': 0,
            'replacement_order_token': 1,
            'quantity': 5000,
            'price': 323.4,
            'time_in_force': 100
        }, {
            'message_type': 'X',
            'order_token': 1,
            'quantity': None
        }]

        for res in testing:

            message_type = res['message_type']

            if message_type == "O":
                order_message = self.parse_order_message(res)
                self.handle_order(res)


            elif message_type == "U":
                replace_message = self.parse_replace_message(res)
                self.handle_replace(res)

            elif message_type == "X":
                cancel_message = self.parse_cancel_message(res)
                self.handle_cancel(res)

            else:
                print("message type error")

            print(self.order_book)
            print(self.token_valid)
            print("next")



    def buy_order(self, indicator, quantity, price, time_in_force, time_received, order_token):
        if price not in self.order_book:
            self.order_book[price] = [[indicator, price, quantity, time_in_force, time_received, order_token]]
        else:
            # if price is already in order book
            self.order_book[price].append([indicator, price, quantity, time_in_force, time_received, order_token])


        pass

    def sell_order(self, indicator, quantity, price, time_in_force, time_received, order_token):
        # same thing as buy_order but this is for the case that problem changes into something harder

        if price not in self.order_book:
            self.order_book[price] = [[indicator, price, quantity, time_in_force, time_received, order_token]]
        else:
            # if price is already in order book
            self.order_book[price].append([indicator, price, quantity, time_in_force, time_received, order_token])



    def get_message_type(self, res):
        return {}


    def parse_order_message(self, res):
        return {}

    def parse_replace_message(self, res):
        return {}

    def parse_cancel_message(self, res):
        return {}

    def check_order_valid(self, order_message):
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

        #check whether invalid order price
        elif order_message['price'] <=0:
            rejected_reasons = "X"
            success = False

        elif order_message['indicator'] != 'B' and order_message['indicator'] != 'S':
            rejected_reasons = "Y"
            success = False

        return success, rejected_reasons



    def handle_order(self, order_message):
        #to check if successful
        success = True
        order_token = order_message['order_token']

        indicator = order_message['indicator']

        quantity = order_message['quantity']

        price = order_message['price']

        time_in_force = order_message['time_in_force']

        time_received = time.time()

        # check whether order_token is not valid
        if order_token != self.curr_order_token+1:
            # Out of sequence token
            # Token out of sequence will be silently ignored
            return

        success, rejected_reasons = self.check_order_valid(order_message)

        if success:
            if indicator == 'B':
                # Buy
                self.buy_order(indicator, quantity, price, time_in_force, time_received, order_token)

            elif indicator == 'S':
                # Sell
                self.sell_order(indicator, quantity, price, time_in_force, time_received, order_token)

            # calls function to output a successful response
            self.output_accepted(order_message)

            # increase the current order token number to match
            curr_order_token += 1

            self.token_valid.append(True)

        else:
            # if invalid

            self.output_rejected(order_message, rejected_reasons)



    def handle_replace(self, replace_message):
        existing_order_token = replace_message['existing_order_token']
        replacement_order_token = replace_message['replacement_order_token']
        quantity = replace_message['quantity']
        price = replace_message['price']
        time_in_force = replace_message['time_in_force']
        time_received = time.time()

        if existing_order_token >= 0 and existing_order_token<= self.curr_order_token and replacement_order_token == self.curr_order_token+1 and self.token_valid[existing_order_token] == True:
            self.curr_order_token = replacement_order_token

            for order_level in self.order_book.values():
                for i, order in enumerate(order_level):
                    # loop through each order to find matching order_token
                    if order[-1] == existing_order_token:
                        indicator = order[0]
                        order_level.pop(i) # remove original from order book

            # increase the current order token number to match new order token number
            curr_order_token += 1

            self.token_valid.append(True)
            self.token_valid[existing_order_token] = False

            if price not in self.order_book:
                self.order_book[price] = [[indicator, price, quantity, time_in_force, time_received, replacement_order_token]]
            else:
                # if price is already in order book
                self.order_book[price].append([indicator, price,quantity,time_in_force, time_received, replacement_order_token])

            self.output_replaced(replace_message)


    def handle_cancel(self, cancel_message):
        order_token = cancel_message['order_token']
        if self.token_valid[order_token]:
            #i.e. if specific order has not been cancelled or replaced
            for order_level in self.order_book.values():
                for i, order in enumerate(order_level):
                    # loop through each order to find matching order_token
                    if order[-1] == order_token:
                        quantity = order[2]
                        order_level.pop(i) # remove original from order book

            self.output_cancelled(cancel_message, 'C', quantity)


    def output_accepted(self, order_message):
        #An Order Accepted Message acknowledges the receipt and acceptance of a valid Enter Order Message
        print(order_message)

    def output_cancelled(self, cancel_message, cancelled_reason, quantity):
        #An Order Canceled Message informs that an order has been canceled. This could be acknowledging a Cancel Order Message, or it could be the result of the order being canceled automatically.

        msg = {
            'message_type': 'C',
            'timestamp': time.time(),
            'order_token': cancel_message['order_token'],
            'decrement quantity': quantity
        }

        print(msg)


    def output_replaced(self, replace_message):
        #An Order Replaced Message acknowledges the receipt and acceptance of a valid Replace Order Message
        #The data fields from the Replace Order Message are echoed back in this message
        print(replace_message)

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
        print(msg)


if __name__ == "__main__":
    a = OrderBook()
    a.test()
