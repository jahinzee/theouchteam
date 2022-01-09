# The OUCH Project - OUCH Server/Client

## Description

This software simulates OUCH Server/Client communication through a script which initialises a central server and another script which simulates clients connecting to the server. Multiple connections can be handled and supported at once.

See future considerations for optimisation and features below.

## Dependencies
Before running, the following dependencies are required:
- tabulate

If running web interface flask, flask_bootstrap, flask_wtf is required.

These dependencies can be installed with pip or another package manager.
```
pip install tabulate

pip install flask
pip install flask_bootstrap
pip install flask_wtf
```

# Usage

Start an instance of *ouch_server.py* first using python. If `debug` is passed as a command line argument, the console output will be in debugging mode as opposed to printing the orderbook once every second.
```
python ouch_server.py
python ouch_server.py debug
```

Then in another terminal/cmd instance, start an instance of *ouch_client.py*. The client will prompt the user for input and pass completed input into the exchange server (NOT IMPLEMENTED YET - USE PROVIDED TEST INPUTS).
```
python ouch_client.py
```

The Client can be initialised with one optional command line argument which specifies a path to a json file containing a sequence of inputs for the client to send to the exchange. Every time the enter key is pressed, one message will be sent in sequence. After all messages have been sent, the client will terminate and disconnect from the server. An example of the json format can be found in the client_inputs folder.

```
python ouch_client.py test_inputs/client_1.json
```

# Optimisation and Future Extensions

- Implement a matching engine for the exchange to support order execution.
- Create a web interface for ease of placing orders.
- A mechanism for opening and closing the exchange.
- Orderbook data structure optimisation using numpy or caching (such as using the **memcached** package).
- Increase client connection thread handling performance using thread pools and connection pools.
- Client message data processing can be made faster by setting up and integrating an Apache Pulsar cluster.

## Client Input JSON Format
The JSON should be structured as follows:
```
{
    "_expected_behaviour": [
        "1. ...",
        "2. ...",
        "3. ...",
        ...
    ],
    "actions": [
        {
            "message_type": "O",
            ...
        },
        {
            "message_type": "U",
            ...
        },
        {
            "message_type": "X",
            ...
        },
        ...
    ]
}
```
- _expected_behaviour: A list of comment strings describing the expected behaviour of the program for each corresponding action. 1.corresponds to the first action etc. This will not be used in the program, and is for documentation purposes only.
- actions: A list of json dictionaries which follow the OUCH protocol's Section 6 (Inbound) specifications. The messages will be sent by the client to the exchange in sequence.

# Web Interface
This interface allows for easier data entry and provides a GUI that more accurately simulates how a typical client will enter order entries.

```
python web_application.py
```
On web browser, type http://127.0.0.1:5000/ to load website

On a separate terminal/cmd instance start an instance of ouch_server.py. Sudo may be needed.

```
python ouch_server.py
```

To create your orders, continually fill in the enter order, replace order and cancel order forms. Once finished, click on the OUCH logo and click submit your order. Continually press enter on command line until and observer appropriate response messages on both terminal console.
