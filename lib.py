"""lib.py

Author:              Adam DeCosta
Class:               CSI-235
Assignment:          Final Project
Date Assigned:       4/09/2018
Due Date:            4/26/2018 11:59 PM

Description:
Helper functions for the final project

Champlain College CSI-235, Spring 2018
The following code was written by Adam DeCosta (adam.decosta@mymail.champlain.edu)
and Kevin Eaton (kevin.eaton@mymail.champlain.edu)
"""

import struct
import asyncio

def message_with_length(message):
    #print(message)
    pack_format = '! I'
    #print(pack_format)
    message_len = struct.pack(pack_format, len(message))
    message = b''.join([message_len, message])
    #print(message)
    return message

async def client_gen(self):
    for key in self.clients:
        yield key

async def get_user_list(self):
    return [key async for key in client_gen(self)]

async def get_items(_list):
    for item in _list:
        yield item