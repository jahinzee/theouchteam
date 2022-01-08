# The OUCH Project - OUCH Server/Client

## Description

This software simulates OUCH Server/Client communication through a script which initialises a central server and another script which simulates clients connecting to the server. Multiple connections can be handled and supported at once.

The server and clients should be hosted on the same local machine.

## Dependencies
Before running, the following dependencies are required:
- pprint
- tabulate

These dependencies can be installed with pip or another package manager.
```
pip install pprint
pip install tabulate
```

# Usage

Start an instance of *ouch_server.py* first using python. If `debug` is passed as a command line argument, the console output will be in debugging mode as oppsoed to printing the orderbook once every second.
```
python ouch_server.py
python ouch_server.py debug
```

Then in another terminal/cmd instance, start an instance of *ouch_client.py*. The client will prompt the user for input and pass completed input into the exchange server (NOT IMPLEMENTED YET - USE PROVIDED TEST INPUTS).
```
python ouch_client.py
```

The Client can be initialised with one optional command line argument which specifies a path to a json file containing a sequence of inputs for the client to send to the exchange. Every time the enter key is pressed, one message will be sent in sequence. After all messages have been sent, the client will prompt for user input as normal. An example of the json format can be found in the client_inputs folder.

```
python ouch_client.py test_inputs/client_1.json
```

## Incomplete Tasks

- Silent mode and csv dump support.
- Docstrings and documentation for new classes.
- User input function.

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

# Future Extensions

- Implement a matching engine for the exchange to support order execution.
- Create a web interface for ease of placing orders.
- A mechanism for opening and closing the exchange.