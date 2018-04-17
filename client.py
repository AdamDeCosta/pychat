# HEADER INFORMATION

import argparse
import asyncio
import struct

class ChatClient(asyncio.Protocol):
    
    def __init__(self, loop):
        self.loop = loop

    def connection_made(self, transport):
       self.transport = transport
       print("Made Connection!")
       
    def data_received(self, data):
        print("Received: " + data)

    def send_message(self, message):
        length = struct.pack('! I', len(message))
        print(length)
        payload = b''.join([length, message])
        self.transport.write(payload)

    def connection_lost(self, exc):
        print('Server closed connection')
        self.loop.stop()

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
        while True: 
            client.send_message(message.encode('ASCII'))
        print(message)


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
