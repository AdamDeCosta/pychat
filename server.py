 # HEADER INFORMATION

import argparse
import asyncio
import struct
import json
import ssl
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

    def data_received(self, data):
        self.data += data

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
                #asyncio.ensure_future(
                #    self.update_message_list(self.data.decode('ASCII')))

                asyncio.ensure_future(
                    self.message_handler(self.data), loop=self.loop)

                self.data = b''
                self.length = None
            else:
                message = self.data[0:self.length]
                # TODO: REMOVE DEBUG
                # TODO: MOVE THIS
                #asyncio.ensure_future(
                #    self.update_message_list(message.decode('ASCII')))

                print("Received message: {}".format(message))

                asyncio.ensure_future(
                    self.message_handler(self.data), loop=self.loop)

                self.data = self.data[self.length:]
                self.length = None
    
    async def update_message_list(self, message):
        Server.messages.get('MESSAGES').extend(message.get('MESSAGES'))

    async def handle_username(self, username):
            user_list = await get_user_list(self)

            # send user_joined to all connections
            payload = json.dumps({'USERS_JOINED': [self.username]}).encode('ASCII')
            await self.message_handler(payload)

            payload = json.dumps(
                {
                    'USERNAME_ACCEPTED': True, 
                    'INFO': 'Welcome!', 
                    'USER_LIST': user_list, 
                    'MESSAGES': Server.messages.get('MESSAGES')
                }).encode('ASCII')
            
            payload = message_with_length(payload)
            self.transport.write(payload)
                

    async def message_handler(self, message):
        message = json.loads(message)

        async for key in get_items(message):

            if key == 'USERS_LEFT' or key == 'USERS_JOINED':
                payload = json.dumps(message).encode('ASCII')
                payload = message_with_length(payload)
                async for client in self.get_clients():
                    client[1].write(payload)

            elif key == 'MESSAGES':
                print(message.get(key))
                await self.update_message_list(message)
                await self.send_message(message.get(key))  # key = 'MESSAGES'

            elif key == 'USERNAME':
                username = message.get(key)  # key = 'USERNAME'
                print(username)
                if await self.is_unique(username):
                    self.username = username
                    await self.handle_username(username)
                    self.clients.update({username: self.transport})
                else:
                    payload = json.dumps(
                    {
                        'USERNAME_ACCEPTED': False, 
                        'INFO': 'Username already in use!'
                    }).encode('ASCII')

                    payload = message_with_length(payload)
                    self.transport.write(payload)

    async def get_clients(self):
        for username, transport in self.clients.items():
            yield (username, transport)

    async def send_message(self, messages):
        all_messages = []
        async for message in get_items(messages):
            if message[1] == 'ALL':
                all_messages.append(message)
            else:
                if message[1] in self.clients:
                    transport = self.clients.get(message[1])
                    payload = json.dumps(
                        {
                            'MESSAGES': [message] 
                        }).encode('ASCII')

                    payload = message_with_length(payload)
                    transport.write(payload)
                else:
                    payload = json.dumps(
                        {
                            'ERROR': 'Client not found'
                        }).encode('ASCII')

                    payload = message_with_length(payload)
                    self.transport.write(payload)
        
        if all_messages:
            payload = json.dumps(
                {
                    'MESSAGES': all_messages
                }).encode('ASCII')
            payload = message_with_length(payload)
            
            async for client in self.get_clients():
                client[1].write(payload)
            

    def connection_lost(self, exc):
        print('Client left: Message {}'.format(exc))
        del self.clients[self.username]
        payload = json.dumps({'USERS_LEFT': [self.username]}).encode('ASCII')
        asyncio.ensure_future(self.message_handler(payload))


    async def is_unique(self, username):
        async for client in client_gen(self):
            if username == client:
                return False
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Asynchronous chat server")
    parser.add_argument('host', help="Hostname or IP")
    parser.add_argument('-p', metavar="port", type=int, default=9000, 
                        help="TCP port (default 9000)")
    parser.add_argument('-a', metavar='cafile', default=None,
                        help='authority: path to CA certificate PEM file')
    parser.add_argument('-s', metavar='certfile', default=None,
                        help='run as server: path to server PEM file')
    args = parser.parse_args()
    
    purpose = ssl.Purpose.SERVER_AUTH
    context = ssl.create_default_context(purpose, cafile=args.a)
    context.load_cert_chain(args.s)

    loop = asyncio.get_event_loop()
    print("{}, {}".format(args.host, args.p))

    coro = loop.create_server(lambda: Server(loop), args.host, args.p)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()