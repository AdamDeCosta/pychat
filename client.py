# HEADER INFORMATION

import argparse
import asyncio
import struct
import json
import time
import calendar
import re
from lib import get_items, message_with_length

class ChatClient(asyncio.Protocol):
    
    def __init__(self, loop):
        self.loop = loop

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
            print("pre: r_length: \n", r_length)
            r_length = struct.unpack('! I', r_length)
            print("post: r_length: \n", r_length[0])
            response = b''
            while True:
                response += socket.recv(r_length[0])
                if len(response) >= r_length[0]:
                    break

            print("pre: response: \n", response)
            response = json.loads(response)
            print("post: response: \n", response)

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
                asyncio.ensure_future(self.message_handler(message), 
                                                           loop=self.loop)
                self.data = b''
                self.length = None
            else:
  
                message = self.data[0:self.length]
                message = json.loads(message.decode('ASCII'))
                asyncio.ensure_future(self.message_handler(message), 
                                                           loop=self.loop)
                self.data = self.data[self.length:]
                self.length = None

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
    parser.add_argument('-p', metavar="port", type=int, default=9000, 
                        help="TCP port (default 1060)")
    args = parser.parse_args()

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
