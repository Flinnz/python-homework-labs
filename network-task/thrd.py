import socket
from threading import Thread
from time import sleep

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind(('localhost',5000))
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.listen()

threads = []

def wait_for_threads():
    for t in threads:
        t.join(1)
        if not t.is_alive():
            threads.remove(t)


def accept_connection():
    while True:
        client_sock, addr = server_sock.accept()
        client_sock.send(b"HELLO %b\r\n" % addr[0].encode())

        print('connected', addr)

        t = Thread(target=client_handling, args=(client_sock,))
        t.start()
        threads.append(t)

        wait_for_threads()

def client_handling(sock):
    while True:
        req = sock.recv(1024)

        if not req:
            sock.close()
            break
            # <<<< Проверить, закрыт ли сокет в этом месте, и если нет - закрыть
        else:
            resp = b'Answer: %s' % req
            sock.send(resp)

try:
    accept_connection()

except Exception as e:
    wait_for_threads()
    print(e)
    server_sock.detach()
    server_sock.close()
server_sock.close()
