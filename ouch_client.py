import sys

from src.client import Client

if __name__ == "__main__":
    if len(sys.argv) == 2:
        orderlist_path = sys.argv[1]
    else:
        orderlist_path = None

    Client(path=orderlist_path)