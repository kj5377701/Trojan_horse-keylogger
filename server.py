# this server didnt finish
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((socket.gethostname(), 1234))

server.listen(5)

serversocket, addr = server.accept()

print('connect from: %s' % addr[0])

data = serversocket.recv(1024)

serversocket.send(data)

serversocket.close()

server.close()
