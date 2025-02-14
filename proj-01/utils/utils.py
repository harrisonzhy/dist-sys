def recv_all(socket, n):
    """Helper function to receive exactly `n` bytes or return None if the connection is closed."""
    data = b""
    while len(data) < n:
        packet = socket.recv(n - len(data))
        if not packet:  # Connection closed
            return None
        data += packet
    return data
