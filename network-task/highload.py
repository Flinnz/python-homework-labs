import socket
from threading import Thread
from time import sleep

address = input('enter address without port: ')
port = int(input('enter port: '))


def start_new_connection(number):
    sock = socket.socket()
    try:
        sock.connect((address, port))
        msg_cnt: int = 0
        while True:
            sock.send(b'Test\n')
            msg_cnt += 1
            data = sock.recv(1024)
    except Exception as e:
        sock.close()
        print(f'socket {str(number)} has failed')
        print(e)


threads = []


def wait_for_threads():
    for thread in threads:
        thread.join(1)
        if not thread.is_alive():
            threads.remove(thread)


cnt = 0
while True:
    new_thread = Thread(target=start_new_connection, args=(int(cnt),))
    new_thread.start()
    threads.append(new_thread)
    #wait_for_threads()
    cnt += 1
    print(f'{len(threads)} alive')
