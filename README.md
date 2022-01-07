# The OUCH Project - OUCH Server/Client

## Description

This software simulates OUCH Server/Client communication through a script which initialises a central server and
another script which simulates clients connecting to the server. Multiple connections can be handled and supported at once.

The server and clients should be hosted on the same local machine.

## Usage

Start an instance of *exchange.py* first using python.
```
python exchange.py
```

Then in another terminal/cmd instance, start an instance of *client.py*. The client will prompt the user for input and pass 
completed input into the exchange server (NOT IMPLEMENTED YET - USE PROVIDED CLIENT INPUTS).
```
python client.py
```

The Client can be initialised with one optional command line argument which specifies a path to a json file containing a sequence of
inputs for the client to send to the exchange. Every time enter is pressed on the keyboard, one message will be sent in sequence.
An example of the json format can be found in the client_inputs folder.

```
python client.py test_inputs/client_1.json
```

## Incomplete Tasks

- **Write more client input test cases.** (HIGHEST PRIORITY - please help with this).
- Silent mode and csv dump support.
- Docstrings and documentation for new classes. (Rayman will take care of this)

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
            "message_type",
            ...
        },
        {
            "message_type",
            ...
        },
        {
            "message_type",
            ...
        },
        ...
    ]
}
```
- _expected_behaviour: A list of comment strings describing the expected output or response from the program for each corresponding action. 1. corresponds to the first action etc. This will not be used in the program, and is for documentation purposes only.
- actions: A list of json dictionaries which follow the OUCH protocol's Section 6 (Inbound) specifications. The messages will be sent by the client to the exchange in sequence.