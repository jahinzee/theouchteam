"""
The OUCH Team
Console + Output Handler

This file uses the following Python dependencies:

tabulate
Copyright (c) 2011-2020 Sergey Astanin and contributors
Full license available at https://github.com/astanin/python-tabulate/blob/master/LICENSE
[!] Before using this file, run "python -m pip install tabulate" in a command window.

"""
import os, sys
from tabulate import tabulate
from datetime import datetime
from src.util import Util

class Console:

    # class constant: default cmd window size (for supported platforms)
    WINDOW_SIZE = [122, 50]

    # class constants: helper vars
    TAB = '\t'
    LIN = '\n'

    # class constant: command list for multi-platform shells
    CMD_LIST = {
        "CLEAR" : {
            "darwin" : "clear",
            "linux" : "clear",
            "linux2" : "clear",
            "win32" : "cls",
            "cygwin" : "cls",
            "msys" : "cls"
        },
        "RESIZE" : {
            "darwin" : "/usr/X11/bin/resize -s {} {}".format(WINDOW_SIZE[0], WINDOW_SIZE[1]),
            "linux" : "resize -s {} {}".format(WINDOW_SIZE[0], WINDOW_SIZE[1]),
            "linux2" : "resize -s {} {}".format(WINDOW_SIZE[0], WINDOW_SIZE[1]),
            "win32" : "MODE {}, {}".format(WINDOW_SIZE[0], WINDOW_SIZE[1]),
            "cygwin" : "MODE {}, {}".format(WINDOW_SIZE[0], WINDOW_SIZE[1]),
            "msys" : "MODE {}, {}".format(WINDOW_SIZE[0], WINDOW_SIZE[1])
        },
        "TITLE" : {
            "darwin" : "echo -n -e \"\\033]0;{}\\\007\"",
            "linux" : "gnome-terminal --title='{}'",
            "linux2" : "gnome-terminal --title='{}'",
            "win32" : "title {}",
            "cygwin" : "title {}",
            "msys" : "title {}"
        }
    }
    
    # class constant: Symbol lookup table
    SYMBOLS = {

        "1" : "BTC",
        "2" : "ETH",
        "3" : "BNB",
        "4" : "SOL",
        "5" : "ADA",
        "6" : "XRP",
        "7" : "DOT",
        "8" : "LUNA",
        "9" : "AVAX",
        "10" : "DOGE",

    }

    # internal storage for tables (sample data; will be reset with __init__)
    internalBook = {
    
        "price" : [
          # B/S                           Symbol
          # [0]           [1]      [2]    [3]            [4]            [5]             [6]        [7]
            ["indicator", "price", "qty", "orderbookID", "timeInForce", "timeReceived", "orderID", "orderToken"]
        ]

    }

    """
    init (*loadfrom)
    - load data from existing order book
    """
    def __init__ (self, loadfrom = {}):
        self.internalBook = loadfrom

    """
    add (newEntry)
    - adds order into appropriate price group
    - silently fails if newEntry is the wrong size
    """
    def add (self, newOrder):
        
        # loose validation
        if len(newOrder) != 8: return None

        # append newEntry into appropriate grouping
        self.internalBook[newOrder[1]].append(newOrder)

    """
    remove (orderIDKey)
    - removes order with the same orderID as orderIDKey
    - silently fails if orderIDKey is invalid
    """
    def remove (self, orderIDKey):

        for priceGroup in self.internalBook:
            for order in self.internalBook[priceGroup]:
                if order[6] == orderIDKey:
                    priceGroup.remove(order)

    """
    replace (orderIDKey, newOrder)
    - replaces order with the same orderID as orderIDKey with newEntry
    - silently fails if orderIDKey or newOrder is invalid
    """
    def replace (self, orderIDKey, newOrder):

        # loose validation
        if len(newOrder) != 8: return None

        for priceGroup in self.internalBook:
            for order in self.internalBook[priceGroup]:
                if order[6] == orderIDKey:
                    priceGroup[order] = newOrder

    """
    print:
    - displays formatted internalTable values in console
    """
    def print (self):
        
        # Reconstruct table as single double array
        singleTable = []
        for priceGroup in self.internalBook:
            singleTable += self.internalBook[priceGroup]

        # Processing order status
        for order in singleTable:

            # Process symbol
            order[3] = self.SYMBOLS[str(order[3])]

        
        # Clear and resize cmd/terminal window
        os.system(self.CMD_LIST["CLEAR"][sys.platform])
        os.system(self.CMD_LIST["RESIZE"][sys.platform])
        os.system(self.CMD_LIST["TITLE"][sys.platform].format("Current Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S (Server Timestamp " + str(Util.get_server_time())) + ")"))
        
        # Print!
        print(tabulate(singleTable, headers = ["Indicator", "Price", "Quantity", "Symbol", "Time in Force", "Time Received", "Order ID", "Order Token", "Order Status"]))    