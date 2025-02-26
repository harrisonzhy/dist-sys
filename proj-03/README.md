# proj-01

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
You should also install `TKinter` using your system's package manager (not `pip`).

## Demo

By default, the demo is set up to run locally. You may configure your desired settings in `config.ini`.

To run the app with one server and one client, start the server in one terminal window and then start the client in another:
```
python3 server.py
python3 client.py
```
The client should send a server message, which is received by the server. On the client side, you should expect in the standard output:
```
Client host: 127.0.0.1
Client port: 5555
Connected to the server.
...
```
On the server side, you should expect in the standard output:
```
Server host: 127.0.0.1
Server port: 5555
Server started on 127.0.0.1:5555
New connection from ('127.0.0.1', 59478)
...
```
The clientside UI should open in another window.
