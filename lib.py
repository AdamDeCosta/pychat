# CREATE HEADER INFO
import struct
import asyncio

def message_with_length(message):
    message_len = struct.pack('! I', len(message))
    message = b''.join([message_len, message])
    return message