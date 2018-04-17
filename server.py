 # HEADER INFORMATION

import asyncio
import struct
import random # remove
import lib

class Server(asyncio.Protocol):

    clients = {}

    def __init__(self):
        self.data = b''
        self.length = None

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

        '''
        # TODO: DEBUG REMOVE AND CHANGE TO USERNAME
        self.username = str(random.randint(0, 1000))
        self.clients.update({self.username : self.transport})
        print(self.clients)
        # END DEBUG
        '''
        
        # TODO: HANDLE USERNAME
        socket = self.transport.get_extra_info('socket')
        socket.setblocking(1)
        name_length = socket.recv(4)
        name_length = struct.unpack('! I', name_length)
        username = socket.recv(name_length[0])
        message = lib.message_with_length(username)
        socket.sendall(message)
        print(b"USERNAME: " + username)
        socket.setblocking(0)

    def data_received(self, data):
        self.data += data

        # TODO: REMOVE DEBUG
        print("Received data: {}".format(data))
        print(len(self.data))
        print("length: {}".format(self.length))
        # END DEBUG

        # TODO: LOOP TO INTERPRET MESSAGES IF TONS ARE RECEIVED SIMULTANEOUSLY
        if not self.length:
            if len(self.data) < 4:
                pass
            else:
                self.length = struct.unpack('! I', self.data[0:4])[0]
                if len(self.data) >= 4:
                    self.data = data[4:]
                else:
                    self.data = b''

        if self.length:
            if len(self.data) < self.length:
                pass
            elif len(self.data) == self.length:
                # TODO: REMOVE DEBUG
                print("Received message: {}".format(self.data))
                self.data = b''
                self.length = None
            else:
                message = self.data[0:self.length]
                # TODO: REMOVE DEBUG
                print("Received message: {}".format(message))
                self.data = self.data[self.length:]
                self.length = None

    def send_message(self, message):
        length = struct.pack('! I', len(message))
        print(length)
        payload = b''.join([length, message])
        yield self.transport.write(payload)

    def connection_lost(self, exc):
        print('Client left: Message {}'.format(exc))

    @asyncio.coroutine
    def check_username(self, username):
        pass


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    coro = loop.create_server(Server, 'localhost', 9000)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()