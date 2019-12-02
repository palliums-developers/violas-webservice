import socket
import struct
import time

class SocketHandler:
    def __init__(self, sock = None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def Connect(self, host, port):
        self.host = host
        self.port = port
        try:
            self.sock.connect((self.host, self.port))
            return True
        except ConnectionRefusedError:
            return False

    def Close(self):
        self.sock.close()

    def Reconnect(self):
        self.Close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for i in range(1, 4):
            print("Reconnect after ", i * 3, " seconds!")

            time.sleep(i * 3)
            if self.Connect(self.host, self.port):
                print("Reconnect success")
                return True

        return False

    def Send(self, msg):
        totalSent = 0

        while totalSent < len(msg):
            try:
                sent = self.sock.send(msg)
                totalSent += sent
            except OSError:
                print("Socket connection broken!")
                if not self.Reconnect():
                    return False

        print("Send msg: ", msg, ", Msg len: ", totalSent)
        return True

    def Recv(self):
        chunks = bytes()

        while True:
            try:
                chunk = self.sock.recv(2048)
            except OSError:
                print("Socket connection broken!")
                if not self.Reconnect():
                    return False, ""

                continue

            if chunk == b"":
                print("Socket is closed by server!")
                if not self.Reconnect():
                    return False, ""

                continue

            chunks += chunk
            msgLen = struct.unpack_from("<H", chunks, 0)

            if msgLen[0] == len(chunks):
                break

        print("Recv msg: ", chunk, ", Msg len: ", len(chunks))
        return True, chunks

    def RecvBigending(self):
        chunks = bytes()
        chunk = b""

        while True:
            try:
                chunk = self.sock.recv(2048)
            except OSError:
                print("Socket connection broken!")
                if not self.Reconnect():
                    return False, ""

                continue

            if chunk == b"":
                print("Socket is closed by server!")
                if not self.Reconnect():
                    return False, ""

                continue

            chunks += chunk
            msgLen = struct.unpack_from("!H", chunks, 0)

            if msgLen[0] == len(chunks):
                break

        print("Recv msg: ", chunk, ", Msg len: ", len(chunks))
        return True, chunks
