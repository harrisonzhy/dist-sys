# proj-03

## Environment Setup

Set up Python virtual environment with Python version 3.13.0.
```
python3 -m venv proj-env
source proj-env/bin/activate
pip3 install -r requirements.txt
```

## Dependencies

We built our implementation to be as lean as possible in terms of dependencies. To install most of the required dependencies, run:
```
pip3 install -r requirements.txt
```

## Demo

By default, the demo is set up to run locally. You may configure your desired settings in `config.ini` and via command line argument.

Run separate instances of `client.py`, specifying the command line arguments like so:
```sh
python3 client.py -h
```
```
usage: client.py [-h] [--host HOST] [--port PORT] [--peers PEERS] [--proba PROBA]

Run the peer client.

options:
  -h, --help     show this help message and exit
  --host HOST    Host for this client to connect to
  --port PORT    Port for this peer to listen on
  --peers PEERS  Comma-separated list of peers in host:port format (e.g.
                 127.0.0.1:5555,127.0.0.1:5556)
  --proba PROBA  Probability (0<=p<=1) to send a message each iteration
```
For instance, you may run the three-peer local network demo (default host is `localhost`, probability is `0.5`):
```
python3 client.py --port 5555 --peers 127.0.0.1:5556,127.0.0.1:5557
python3 client.py --port 5556 --peers 127.0.0.1:5555,127.0.0.1:5557
python3 client.py --port 5557 --peers 127.0.0.1:5555,127.0.0.1:5556
```
You should see some messages exchanged in the standard output and callbacks invoked on all sides. 
