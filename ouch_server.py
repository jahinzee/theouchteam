import sys

from src.Exchange import Exchange

if __name__ == "__main__":
    exchange = None
    if len(sys.argv) == 2:
        if sys.argv[1] == "debug":
            # Exchange outputs using debug mode.
            exchange = Exchange(debug="dump")
        elif sys.argv[1] == "none":
            # Exchange won't output anything.
            exchange = Exchange(debug="none")
        else:
            raise Exception("Command line argument should be either 'dump' or 'none'")
    else:
        exchange = Exchange()
    exchange.open_exchange()
    input() # Pressing the enter key will cause the server process to terminate.
    exchange.close_exchange()