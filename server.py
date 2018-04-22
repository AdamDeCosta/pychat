 # HEADER INFORMATION

import asyncio
import struct
import json
from lib import *

class Server(asyncio.Protocol):

    clients = {}
    messages = {}

    def __init__(self, loop):
        self.data = b''
        self.length = None
        self.loop = loop
        if not Server.messages:
            Server.messages = {'MESSAGES': []}

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        self.username_handler()

    def username_handler(self):
        socket = self.transport.get_extra_info('socket')
        socket.setblocking(1)
        while True:
            name_length = socket.recv(4)
            name_length = struct.unpack('! I', name_length)
            username = socket.recv(name_length[0])
            username = username.decode('ASCII')

            if self.is_unique(username):
                self.username = username
                break
            else:
                payload = json.dumps({'USERNAME_ACCEPTED': False, 'INFO': 'Username already in use!'}).encode('ASCII')
                payload = message_with_length(payload)
                socket.sendall(payload)

        # Send welcome message
        user_list = get_user_list(self)

        # send user_joined to all connections
        payload = json.dumps({'USERS_JOINED': [self.username]}).encode('ASCII')
        asyncio.ensure_future(self.send_message(payload))

        payload = json.dumps({'USERNAME_ACCEPTED': True, 'INFO': 'Welcome!', 'USER_LIST': user_list, 'MESSAGES': Server.messages.get('MESSAGES')}).encode('ASCII')
        payload = message_with_length(payload)
        socket.sendall(payload)
        self.clients.update({username: self.transport})
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
                asyncio.ensure_future(self.update_message_list(self.data.decode('ASCII')))
                asyncio.ensure_future(self.send_message(self.data), loop=self.loop)
                self.data = b''
                self.length = None
            else:
                message = self.data[0:self.length]
                # TODO: REMOVE DEBUG
                asyncio.ensure_future(self.update_message_list(message.decode('ASCII')))
                print("Received message: {}".format(message))
                asyncio.ensure_future(self.send_message(self.data), loop=self.loop)
                self.data = self.data[self.length:]
                self.length = None
    
    async def update_message_list(self, message):
        message = json.loads(message)
        Server.messages.get('MESSAGES').extend(message.get('MESSAGES'))


    async def get_clients(self):
        for username, transport in self.clients.items():
            yield (username, transport)

    async def send_message(self, message, all=True):
        payload = message_with_length(message)

        if all:
            async for client in self.get_clients():
                print("Sent message to: {}".format(client[0]))
                client[1].write(payload)

    def connection_lost(self, exc):
        print('Client left: Message {}'.format(exc))
        del self.clients[self.username]
        payload = json.dumps({'USERS_LEFT': [self.username]}).encode('ASCII')
        asyncio.ensure_future(self.send_message(payload))


    def is_unique(self, username):
        for key in self.clients:
            if key == username:
                return False
        return True

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    coro = loop.create_server(lambda: Server(loop), 'localhost', 9000)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()