import socket
import threading
import os
import select

fileRecieving = threading.Event()
closing = threading.Event()
fileRecieving.set()

def fileRCV(sock, name, size):
    fileRecieving.clear()
    print(f"Currently recieving file {name}")
    file = b""
    total = 0
    while total<size:
        rcv = sock.recv(min(1024,size-total))
        file+=rcv
        total+=len(rcv)
    print("Done recieving file, printing file")
    print(file.decode())
    fileRecieving.set()

def listen(sock):
    while True:
        if select.select([sock], [], [])[0]:
            if (closing.is_set()):
                break   
            try:
                mtype, message, *size = sock.recv(1024).decode('utf-8').split('|')
                if (size):
                    size = int(size[0])
                if (mtype == 'msg'):
                    print(f"Server: {message}")
                else:
                    fileRCV(sock,message,size)
            except:
                0

def fileSend(sock, name, size):
    sock.send(f'{f"file|{name}|{size}":<1024}'.encode())
    with open(name, 'r') as f:
        while (size>0):
            sock.send(f.read(1024).encode('utf-8'))
            size-=1024

def sender(sock):
    while True:
        fileRecieving.wait()

        message = input()
        if (message[:5] == 'file:'):
            _, name = message.split(':')
            if (os.path.isfile(name)):
                fileSend(sock, name, os.path.getsize(name))
            else:
                print(f"{name} is not a file")
        else:
            sock.send(f"msg|{message}".encode())
            print(f"Client: {message}")
            if (message == "Bye from client"):
                print(sock.recv(1024).decode().split('|')[-1])
                closing.set()
                break


if (os.path.isfile("settings.txt")):
    try:
        with open("settings.txt", "r") as f:
            lines = f.read().split('\n')
            IP = lines[0].split(':')[-1]
            port = int(lines[1].split(':')[-1])
    except:
        print(f"Your settings .txt may be set up wrong, please make sure it follows this format \nIP:x.x.x.x \nPort:xxx")
else:
    print("There is no settings.txt please create a file 'settings.txt' in the running directory with the format: \nIP:x.x.x.x \nPort:xxx")
    exit()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect((IP, port))
    client.send("Hello from client".encode())
    recieving = threading.Thread(target=listen, args={client,})
    sending = threading.Thread(target=sender, args={client,})
    recieving.start()
    sending.start()
    
    sending.join()
    recieving.join()
finally:
    client.close()