# CREATE HEADER INFO
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

def get_user_list(self):
    return [key for key in self.clients]

async def get_items(_list):
    for item in _list:
        yield item