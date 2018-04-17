 # HEADER INFORMATION

import asyncio
import struct

class Server(asyncio.Protocol):

    def __init__(self):
        self.data = b''
        self.length = None

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        self.data += data
        print("Received data: {}".format(data))
        print(len(self.data))
        print("length: {}".format(self.length))
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
                print("Received message: {}".format(self.data))
                self.data = b''
                self.length = None
            else:
                message = self.data[0:self.length]
                print("Received message: {}".format(message))
                self.data = self.data[self.length:]
                self.length = None

    def connection_lost(self, exc):
        print('Client left: Message {}'.format(exc))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    coro = loop.create_server(Server, 'localhost', 9000)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()