import socket
import os
import struct
from ctypes import *

# listen to
host = "10.1.199.20"


# mimic C IP header struct
class IP(Structure):
    _fields_ = [("ihl", c_ubyte, 4), ("version", c_ubyte, 4), ("tos", c_ubyte), ("len", c_ushort), ("id", c_ushort),
                ("offset", c_ushort), ("ttl", c_ubyte), ("protocol_num", c_ubyte), ("sum", c_ushort), ("src", c_ulong),
                ("dst", c_ulong)]

    def __new__(self, socket_buffer=None):
        return self.from_buffer_copy(socket_buffer)

    def __init__(self, socket_buffer=None):
        # protocol mapping
        self.protocol_map = {1: "ICMP", 6: "TCP", 17: "UDP"}

        # readable IP address
        self.src_address = socket.inet_ntoa(struct.pack("<L", self.src))
        self.dst_address = socket.inet_ntoa(struct.pack("<L", self.dst))

        # readable protocol
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except:
            self.protocol = str(self.protocol_num)


# create raw socket to public interface
if os.name == "nt":
    socket_protocol = socket.IPPROTO_IP
else:
    socket_protocol = socket.IPPROTO_ICMP

sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
sniffer.bind((host, 0))

# we hope captured packet includes IP headers
sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

# for windows, we need to set IOCTL
if os.name == "nt":
    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

try:
    while True:
        # read a packet
        raw_buffer = sniffer.recvfrom(65565)[0]

        # construct IP header from first 20 bytes
        ip_header = IP(raw_buffer[0:20])

        print "Protocol: %s %s -> %s" % (ip_header.protocol, ip_header.src_address, ip_header.dst_address)

except KeyboardInterrupt:
    # close IOCTL for windows
    if os.name == "nt":
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
