"""client.py

    Run python client.py [args]

Author:              Adam DeCosta & Kevin Eaton
Class:               CSI-235
Assignment:          Final Project
Date Assigned:       4/09/2018
Due Date:            4/26/2018 11:59 PM

Description:
An asynchronous chat client used to connect to the corresponding server

Champlain College CSI-235, Spring 2018
The following code was written by Adam DeCosta (adam.decosta@mymail.champlain.edu)
and Kevin Eaton (kevin.eaton@mymail.champlain.edu)
"""

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
        """
        An asynchronous chat client used to connect to the corresponding server
        """
        self.loop = loop
        self.logged_in = False

    def connection_made(self, transport):
        """
        Does setup when connection to the server is made
        """
        self.data = b''
        self.length = None
        self.transport = transport
        self.user_list = []
        print("Made Connection!")

        # Initial username sending
        self.username = input("Enter username: ")
        payload = json.dumps({'USERNAME': self.username})
        payload = message_with_length(payload.encode('ASCII'))
        self.transport.write(payload)

    def data_received(self, data):
        """
        Receive data from the server and then call the message handler
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
                message = json.loads(self.data[:self.length].decode('ASCII'))
                asyncio.ensure_future(
                    self.message_handler(message), 
                    loop=self.loop)
                self.data = self.data[self.length:]
                while True:
                    if(len(self.data) < 4):
                        self.length = None
                        break 
                    else:
                        self.length = struct.unpack('! I', self.data[0:4])[0]
                        self.data = self.data[4:]
                        if self.length > len(self.data):
                            break
                        else:
                            message = json.loads(
                                self.data[:self.length].decode('ASCII'))
                            asyncio.ensure_future(
                                self.message_handler(message), 
                                loop=self.loop)
                            self.data = self.data[:self.length]

    def send_message(self, message):
        """
        Sends messages to the server
        """
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
        """
        Handles messages received from the server
        """
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
                print(self.user_list)

        username_accepted = message.get('USERNAME_ACCEPTED')
        if username_accepted == False:
            print("Server: {}".format(message.get('INFO')))
            self.username = input("Enter a username: ")
            payload = json.dumps({'USERNAME': self.username})
            payload = message_with_length(payload.encode('ASCII'))
            self.transport.write(payload)
        elif username_accepted == True:
            self.logged_in = True
            print("Server: {}".format(message.get("INFO")))

        user_list = message.get('USER_LIST')
        if user_list:
            self.user_list = user_list
            print(self.user_list)

        error = message.get('ERROR')
        if error:
            output([['Server', None, time.gmtime(), error]])

    def connection_lost(self, exc):
        """
        If server goes down, display error and stop the client.
        """
        if exc:
            print('Server disconnected: Message {}'.format(exc))
        else:
            print("Server disconnected.")
        self.loop.stop()


def output(messages):
    """
    Output to whatever we have our front end to be (console)
    """
    for m in messages:
        print("{}: \tSENT TO {} \t {}".format(m[0],m[1], m[3]))


@asyncio.coroutine
def handle_user_input(loop, client):
    """ 
    reads from stdin in separate thread
    if user inputs 'quit' stops the event loop
    or if user inputs '/list' prints client list
    otherwise just echos user input
    """
    while True:
        if client.logged_in:
            message = yield from loop.run_in_executor(None, input, "> ")
            if message == "quit":
                loop.stop()
                return
            elif message.lower() == "/list":
                print(client.user_list)
            else:
                yield client.send_message(message)
        else:
            yield


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

    coro = loop.create_connection(lambda: client, args.host, args.p, ssl=context)
    loop.run_until_complete(coro)

    try:
        loop.run_until_complete(handle_user_input(loop, client))
    finally:
        loop.close()
