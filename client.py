# HEADER INFORMATION

import argparse
import asyncio
import struct
import json
import time
import calendar
import re
import ssl
from lib import get_items, message_with_length

class ChatClient(asyncio.Protocol):
    
    def __init__(self, loop):
        self.loop = loop
        print('init')

    def connection_made(self, transport):
        self.data = b''
        self.length = None
        self.transport = transport
        print("Made Connection!")

        socket = self.transport.get_extra_info('socket')
        socket.setblocking(1)
        while True:
            self.username = input("Enter username: ")
            payload = '{"USERNAME": "' + self.username + '"}'
            payload = message_with_length(payload.encode('ASCII'))
            print(payload)
            socket.sendall(payload)

            r_length = socket.recv(4)
            print(r_length)
            r_length = struct.unpack('! I', r_length)
            response = b''
            while True:
                response += socket.recv(r_length[0])
                if len(response) >= r_length[0]:
<<<<<<< HEAD
                    break

            response = json.loads(response)
=======
                    break;
            #print("pre: response: \n", response)
            response = json.loads(response)
            #print("post: response: \n", response)
>>>>>>> upstream/master

            if response.get('USERNAME_ACCEPTED'):
                #print(response.get('INFO'))
                self.user_list = response.get('USER_LIST')
                #print(response)
                self.messages = response.get('MESSAGES')
                output(self.messages)
                break
            else:
                print(response.get('INFO'))

        socket.setblocking(0)
       
    def data_received(self, data):
        '''

        '''
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
                message = json.loads(self.data[:self.length].decode('ASCII'))
                asyncio.ensure_future(self.message_handler(message), loop=self.loop)
                self.data = self.data[self.length:]
                while True:
                    if(len(self.data) < 4):
                        self.length = None;
                        break; 
                    else:
                        self.length = struct.unpack('! I', self.data[0:4])[0]
                        self.data = self.data[4:]
                        if self.length > len(self.data):
                            break
                        else:
                            message = json.loads(self.data[:self.length].decode('ASCII'))
                            asyncio.ensure_future(self.message_handler(message), loop=self.loop)
                            self.data = self.data[:self.length]
            

    def send_message(self, message):
        dest = re.search(r'@\w+', message)  # returns when @<word> is found
        if dest:
            message = json.dumps(
                { 'MESSAGES': 
                    [
                        (self.username, 
                         dest.group()[1:], 
                         calendar.timegm(time.gmtime()), 
                         message)
                     ]
                }).encode('ASCII')
        else:
            message = json.dumps(
                { 'MESSAGES': 
                    [
                        (self.username, 'ALL', 
                        calendar.timegm(time.gmtime()), 
                        message)
                    ]
                }).encode('ASCII')

        message = message_with_length(message)
        self.transport.write(message)

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
        error = message.get('ERROR')
        if error:
            output([['Server', None, time.gmtime(), error]])

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
    parser.add_argument('host', help="Hostname or IP", default="csi235.site")
    parser.add_argument('-p', metavar="port", type=int, default=9001, 
                        help="TCP port (default 9001)")
    parser.add_argument('-a', metavar='cafile', default=None,
                        help='authority: path to CA certificate PEM file')
    args = parser.parse_args()

    purpose = ssl.Purpose.CLIENT_AUTH
    context = ssl.create_default_context(purpose, cafile=args.a)

    # Loop information and running
    loop = asyncio.get_event_loop()
    print("{}, {}".format(args.host, args.p))

    client = ChatClient(loop)

    coro = loop.create_connection(lambda: client, args.host, args.p)
    loop.run_until_complete(coro)

    loop.run_until_complete(handle_user_input(loop, client))
    
    try:
        loop.run_forever()
    finally:
        loop.close()
