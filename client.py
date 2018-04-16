# HEADER INFORMATION

import argparse
import asyncio

class ChatClient(asyncio.Protocol):
    
    def data_received(self, data):
        print("Received: " + data)

@asyncio.coroutine
def handle_user_input(loop):
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

    client = ChatClient()

    coro = loop.create_connection(lambda: client, args.host, args.p)
    loop.run_until_complete(handle_user_input(loop))

    try:
        loop.run_forever()
    finally:
        loop.close()
