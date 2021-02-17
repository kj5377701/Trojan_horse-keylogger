import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((socket.gethostname(), 1234))

client.send(b'hello world')

data = client.recv(1024)

print(data)

client.close()
