import sys

from src.exchange import Exchange

if __name__ == "__main__":
    exchange = None
    if len(sys.argv) == 2:
        if sys.argv[1] == "debug":
            exchange = Exchange(debug=True)
    else:
        exchange = Exchange()
    exchange.open_exchange()
    input()
    exchange.close_exchange()