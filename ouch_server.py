import sys

from src.Exchange import Exchange

if __name__ == "__main__":
    exchange = None
    if len(sys.argv) == 2:
        if sys.argv[1] == "debug":
            exchange = Exchange(debug="dump")
        elif sys.argv[1] == "none":
            exchange = Exchange(debug="none")
        else:
            raise Exception("Command line argument should be either 'dump' or 'none'")
    else:
        exchange = Exchange()
    exchange.open_exchange()
    input()
    exchange.close_exchange()