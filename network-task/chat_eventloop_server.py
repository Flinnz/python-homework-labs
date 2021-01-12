import socket
from select import select
from time import sleep

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind(('localhost', 5001))
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.listen()

mon_sockets = []


def accept_connection(sock):
    client_sock, address = sock.accept()
    client_sock.send(b"HELLO %b\r\n" % address[0].encode())

    print('connected', address)

    mon_sockets.append(client_sock)


def send_message(client_sock):
    req = client_sock.recv(1024)
    if req:
        resp = b'%s: %s' % (str.encode(str(client_sock.getpeername()[0]) + str(client_sock.getpeername()[1])), req)
        for sock in mon_sockets:
            if sock is server_sock or sock is client_sock:
                continue
            sock.send(resp)

    else:
        client_sock.close()
        mon_sockets.remove(client_sock)


def event_loop():
    while True:
        rd_socks, _, _ = select(mon_sockets, [], [])

        for sk in rd_socks:
            if sk is server_sock:
                accept_connection(sk)
            else:
                send_message(sk)


if __name__ == "__main__":
    try:
        mon_sockets.append(server_sock)
        event_loop()

        # accept_connection()
    except Exception as e:
        print(e)
        server_sock.detach()
        server_sock.close()
    except KeyboardInterrupt as e:
        print(e)
        server_sock.detach()
        server_sock.close()

    server_sock.close()
