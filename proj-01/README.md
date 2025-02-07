# proj-01

## Environment Setup

Set up Python virtual environment with Python version 3.13.0.
```
python3 -m venv proj-env
source proj-env/bin/activate
pip3 install -r requirements.txt
```

## Demo

To run the demo with one server and one client (viewing their standard outputs), start the server in one terminal window and then start the client in another:
```
python3 server.py
python3 client.py
```
The client should send a server message, which is received by the server. On the client side, you should expect:
```
Client host: 127.0.0.1
Client port: 5555
Connected to the server.
Send server message...
```
On the server side, you should expect:
```
Server host: 127.0.0.1
Server port: 5555
Server started on 127.0.0.1:5555
New connection from ('127.0.0.1', 59478)
Received message type 00000000 from ('127.0.0.1', 59478): Hello World
Action OK
```