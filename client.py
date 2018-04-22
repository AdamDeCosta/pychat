# HEADER INFORMATION

import argparse
import asyncio
import struct
import json
import time
from lib import get_items, message_with_length

class ChatClient(asyncio.Protocol):
    
    def __init__(self, loop):
        self.loop = loop

    def connection_made(self, transport):
        self.data = b''
        self.length = None
        self.transport = transport
        print("Made Connection!")

        # TODO: HANDLE USERNAME
        socket = self.transport.get_extra_info('socket')
        socket.setblocking(1)
        while True:
            self.username = input("Enter username: ")
            payload = message_with_length(self.username.encode('ASCII'))
            socket.sendall(payload)


            r_length = socket.recv(4)
            r_length = struct.unpack('! I', r_length)

            response = socket.recv(r_length[0]).decode('ASCII')
            response = json.loads(response)

            if response.get('USERNAME_ACCEPTED'):
                print(response.get('INFO'))
                self.user_list = response.get('USER_LIST')
                print(response)
                self.messages = response.get('MESSAGES')
                output(self.messages)
                break
            else:
                print(response.get('INFO'))

        socket.setblocking(0)
       
    def data_received(self, data):
        self.data += data

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
                message = json.loads(self.data.decode('ASCII'))
                asyncio.ensure_future(self.message_handler(message), loop=self.loop)
                self.data = b''
                self.length = None
            else:
                message = self.data[0:self.length]
                message = json.loads(message.decode('ASCII'))
                asyncio.ensure_future(self.message_handler(message), loop=self.loop)
                self.data = self.data[self.length:]
                self.length = None

    def send_message(self, message):

        message = json.dumps({ 'MESSAGES': [(self.username, 'ALL', time.gmtime(), message)]})

        payload = message_with_length(message.encode('ASCII'))
        self.transport.write(payload)

    def connection_lost(self, exc):
        output('Server closed connection')
        self.loop.stop()

    async def message_handler(self, message):
        messages = message.get('MESSAGES')
        if messages:
            output(messages)

        users_joined = message.get('USERS_JOINED')
        if users_joined:
            async for user in get_items(users_joined):
                self.user_list.append(user)
                print("User: {} has joined.".format(user))
            print(self.user_list)
        
        users_left = message.get('USERS_LEFT')
        if users_left:
            async for user in get_items(users_left):
                self.user_list.remove(user)
                print("User: {} has left.".format(user))

def output(messages):
    '''
    Output to whatever we have our front end to be
    '''
    for m in messages:
        print("{}: {}".format(m[0], m[3]))

        

@asyncio.coroutine
def handle_user_input(loop, client):
    """ 
    reads from stdin in separate thread
    if user inputs 'quit' stops the event loop
    otherwise just echos user input
    """

    while True:
        message = yield from loop.run_in_executor(None, input, "> ")
        if message == "quit":
            loop.stop()
            return
        client.send_message(message)


if __name__ == "__main__":
    # Get arguments from command line
    parser = argparse.ArgumentParser(description="Asynchronous chat client")
    parser.add_argument('host', help="Hostname or IP")
    parser.add_argument('-p', metavar="port", type=int, default=1060, 
                        help="TCP port (default 1060)")
    args = parser.parse_args()

    # Loop information and running
    loop = asyncio.get_event_loop()
    print("{}, {}".format(args.host, args.p))

    client = ChatClient(loop)

    coro = loop.create_connection(lambda: client, 'localhost', 9000)
    loop.run_until_complete(coro)

    loop.run_until_complete(handle_user_input(loop, client))
    
    try:
        loop.run_forever()
    finally:
        loop.close()
