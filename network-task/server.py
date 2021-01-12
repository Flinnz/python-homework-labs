import socket
from time import sleep

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind(('localhost',5000))
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.listen()

try:
    while True:
        client_sock, addr = server_sock.accept()
        client_sock.send(b"HELLO %b\r\n" % addr[0].encode())

        print('connected', addr)

        while True:
            req = client_sock.recv(1024)

            if not req:
                break
            else:
                resp = b'Answer: %s' % req
                client_sock.send(resp)

except Exception as e:
    print(e)
    server_sock.detach()
    server_sock.close()
server_sock.close()
