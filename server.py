"""server.py

    Run python server.py [args]

Author:              Adam DeCosta
Class:               CSI-235
Assignment:          Final Project
Date Assigned:       4/09/2018
Due Date:            4/26/2018 11:59 PM

Description:
An asynchronous chat server which is to be connected to by chat clients

Champlain College CSI-235, Spring 2018
The following code was written by Adam DeCosta (adam.decosta@mymail.champlain.edu)
and Kevin Eaton (kevin.eaton@mymail.champlain.edu)
"""

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
        """
        An asynchronous chat server which is to be connected to by chat clients
        """
        self.data = b''
        self.length = None
        self.loop = loop
        if not Server.messages:
            Server.messages = {'MESSAGES': []}

    def connection_made(self, transport):
        """
        Initial connection made configuration
        """
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        """
        Handles data being received from clients
        """
        self.data += data
        if len(self.data) < 4:
            pass
        else:
            if not self.length:
                self.length = struct.unpack('! I', self.data[:4])[0]
                self.data = self.data[4:]
            if self.length > len(self.data):
                pass
            else:
                message = self.data[:self.length].decode('ASCII')
                asyncio.ensure_future(
                    self.message_handler(message), 
                    loop=self.loop)
                self.data = self.data[self.length:]
                while True:
                    if(len(self.data) < 4):
                        self.length = None
                        break; 
                    else:
                        self.length = struct.unpack('! I', self.data[0:4])[0]
                        self.data = self.data[4:]
                        if self.length > len(self.data):
                            break
                        else:
                            message = self.data[:self.length].decode('ASCII')
                            asyncio.ensure_future(
                                self.message_handler(message), 
                                loop=self.loop)
                            self.data = self.data[:self.length]

    async def update_message_list(self, messages):
        """
        Extends the server message list
        """
        Server.messages.get('MESSAGES').extend(messages)

    async def handle_username(self, username):
        """
        Handles when a unique username is sent to the server
        """
        user_list = await get_user_list(self) or []

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
        """
        Handles messages sent to the server
        """
        message = json.loads(message)
        async for key in get_items(message):

            if key == 'USERS_LEFT' or key == 'USERS_JOINED':
                payload = json.dumps(message).encode('ASCII')
                payload = message_with_length(payload)
                async for client in self.get_clients():
                    client[1].write(payload)

            elif key == 'MESSAGES':
                await self.send_message(message.get(key))  # key = 'MESSAGES'

            elif key == 'USERNAME':
                username = message.get(key)  # key = 'USERNAME'

                if await self.is_unique(username):
                    self.username = username
                    self.clients.update({username: self.transport})
                    await self.handle_username(username)

                else:
                    payload = json.dumps(
                    {
                        'USERNAME_ACCEPTED': False, 
                        'INFO': 'Username already in use!'
                    }).encode('ASCII')

                    payload = message_with_length(payload)
                    self.transport.write(payload)

    async def get_clients(self):
        """
        Generator to get the list of clients for the server
        """
        for username, transport in self.clients.items():
            yield (username, transport)

    async def send_message(self, messages):
        """
        Sends messages to the correct client (ALL or Private)
        """
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
            await self.update_message_list(all_messages)
            
            async for client in self.get_clients():
                client[1].write(payload)
            

    def connection_lost(self, exc):
        """
        Handles clients disconnecting from the server
        """
        print('Client left: Message {}'.format(exc))
        del self.clients[self.username]
        payload = json.dumps({'USERS_LEFT': [self.username]}).encode('ASCII')
        asyncio.ensure_future(self.message_handler(payload))


    async def is_unique(self, username):
        """
        Checks if the username is a unique key in self.clients
        """
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
    
    purpose = ssl.Purpose.CLIENT_AUTH
    context = ssl.create_default_context(purpose, cafile=args.a)
    context.load_cert_chain(args.s)

    loop = asyncio.get_event_loop()
    print("{}, {}".format(args.host, args.p))

    coro = loop.create_server(lambda: Server(loop), args.host, args.p, ssl=context)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()