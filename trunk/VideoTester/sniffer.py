# coding=UTF8
## This file is part of VideoTester
## See http://video-tester.googlecode.com for more information
## Copyright 2011 Iñaki Úcar <i.ucar86@gmail.com>
## This program is published under a GPLv3 license

from scapy.all import *
from time import time
from config import VTLOG

class RTSPi(Packet):
    name = "RTSP interleaved"
    fields_desc = [ ByteField("magic", 24),
                    ByteField("channel", 0),
                    ShortField("length", None) ]

class Sniffer:
    def __init__(self, conf):
        self.conf = conf
        self.clock = None
        self.ptype = None
        self.cap = None
        self.lengths = []
        self.times = []
        self.sequences = []
        self.timestamps = []
        self.ping = {0:{}, 1:{}, 2:{}, 3:{}}
    
    def run(self, q, gui=False):
        VTLOG.info("Starting sniffer...")
        expr='host ' + self.conf['ip']
        cap = self.sniff(iface=self.conf['iface'], filter=expr)
        location = self.conf['tempdir'] + self.conf['num'] + '.cap'
        wrpcap(location, cap)
        q.put(location)
        VTLOG.info("Sniffer stopped")

    def sniff(count=0, prn = None, lfilter=None, *arg, **karg):
        #sniff() Scapy function modification
        c = 0
        L2socket = conf.L2listen
        s = L2socket(type=ETH_P_ALL, *arg, **karg)
        lst = []
        remain = None
        VTLOG.debug("Sniffer: loop started. Sniffing...")
        while 1:
            sel = select([s],[],[],remain)
            if s in sel[0]:
                p = s.recv(MTU)
                if p is None:
                    break
                #This line fixes the lack of timing accuracy
                p.time = time()
                if lfilter and not lfilter(p):
                    continue
                lst.append(p)
                aux = str(p)
                #Look for a TEARDOWN packet to stop the loop
                if (aux.find("TEARDOWN") != -1) and (aux.find("Public:") == -1):
                    VTLOG.debug("TEARDOWN found!")
                    break
                c += 1
                if prn:
                    r = prn(p)
                    if r is not None:
                        print r
                if count > 0 and c >= count:
                    break
        s.close()
        VTLOG.debug("Sniffer: loop terminated")
        return PacketList(lst,"Sniffed")
    
    def parsePkts(self):
        VTLOG.info("Starting packet parser...")
        if self.conf['protocols'] == "tcp":
            self.__parseTCP()
        else:
            self.__parseUDP()
        self.__normalize()
        a = str(self.sequences[-1]-len(self.sequences)+1)
        b = str(len(self.sequences))
        VTLOG.debug(b + " RTP packets received, " + a + " losses")
        VTLOG.info("Packet parser stopped")
        return self.lengths, self.times, self.sequences, self.timestamps, self.ping
    
    def __prepare(self, p):
        play = False
        if p.haslayer(ICMP):
            self.ping[p[ICMP].seq][p[ICMP].type] = p.time
        elif str(p).find("Content-Type: application/sdp") != -1:
            lines = str(p[TCP].payload).splitlines()
            for line in lines:
                if line.find("m=video") != -1:
                    fields = line.split(" ")
                    self.ptype = int(fields[-1])
                    VTLOG.debug("Payload type found!")
            for line in lines:
                if line.find("rtpmap:" + str(self.ptype)) != -1:
                    fields = line.split("/")
                    self.clock = int(fields[-1])
                    VTLOG.debug("Clock rate found!")
        elif (str(p).find("PLAY") != -1) and (str(p).find("Public:") == -1):
            play = True
            VTLOG.debug("PLAY found!")
        return play
    
    def __bubbleSort(self, list, list1=None, list2=None):
        #Bubble sort algorithm modification
        def swap(a, b):
            return b, a
        
        n = len(list)
        for i in range(0, n):
            for j in range(n-1, i, -1):
                if list[j-1] > list[j]:
                    list[j-1], list[j] = swap(list[j-1], list[j])
                    if list1:
                        list1[j-1], list1[j] = swap(list1[j-1], list1[j])
                    if list2:
                        list2[j-1], list2[j] = swap(list2[j-1], list2[j])
        return list, list1, list2
    
    def __parseUDP(self):
        def extract(p):
            ptype = ord(str(p[UDP].payload)[1]) & 0x7F #Delete RTP marker
            p[UDP].decode_payload_as(RTP)
            if ptype == self.ptype:
                #Avoid duplicates while running on loopback interface
                if p[RTP].sequence not in self.sequences:
                    self.lengths.append(p.len)
                    self.times.append(p.time)
                    self.sequences.append(p[RTP].sequence)
                    self.timestamps.append(p[RTP].timestamp)
                    VTLOG.debug("UDP/RTP packet found. Sequence: " + str(p[RTP].sequence))
        
        play = False
        for p in self.cap:
            if p.haslayer(IP):
                if (str(p).find("PAUSE") != -1) and play:
                    VTLOG.debug("PAUSE found!")
                    break
                if not play:
                    play = self.__prepare(p)
                elif play and (p[IP].src == self.conf['ip']) and (p.haslayer(UDP)) and (str(p).find("GStreamer") == -1):
                    extract(p)
        self.__bubbleSort(self.sequences, self.times, self.timestamps)
        VTLOG.debug("Sequence list sorted")
    
    def __parseTCP(self):
        def extract(p):
            #Extract many RTSP packets from TCP stream recursively
            fin = False
            a = p[RTSPi].length
            b = p[RTSPi].payload
            c = str(b)[0:a]
            loss = c.find('PACKETLOSS')
            if loss == -1:
                #No loss: look inside then
                ptype = ord(str(p[RTSPi].payload)[1]) & 0x7F #Delete RTP marker
                if ptype == self.ptype:
                    aux = str(p).split('ENDOFPACKET')
                    p[RTSPi].decode_payload_as(RTP)
                    #Avoid duplicates while running on loopback interface
                    if p[RTP].sequence not in self.sequences:
                        self.lengths.append(int(aux[2]))
                        self.times.append(float(aux[1]) / 1000000)
                        self.sequences.append(p[RTP].sequence)
                        self.timestamps.append(p[RTP].timestamp)
                        VTLOG.debug("TCP/RTP packet found. Sequence: " + str(p[RTP].sequence))
            else:
                #Avoid PACKETLOSS
                a = loss + len('PACKETLOSS')
                VTLOG.debug("PACKETLOSS!")
            p = RTSPi(str(b)[a:len(b)])
            ptype = ord(str(p[RTSPi].payload)[1]) & 0x7F
            #Let's find the next RTSP packet
            while not fin and not ((p[RTSPi].magic == 0x24) and (p[RTSPi].channel == 0x00) and (ptype == self.ptype)):
                stream = str(p)
                if stream.find('PACKETLOSS') == 0:
                    #Avoid PACKETLOSS
                    stream = stream[len('PACKETLOSS'):len(stream)]
                    VTLOG.debug("PACKETLOSS!")
                else:
                    #Find next packet
                    stream = stream[1:len(stream)]
                if len(stream) > 5:
                    p = RTSPi(stream)
                    ptype = ord(str(p[RTSPi].payload)[1]) & 0x7F
                else:
                    #Yep! We're done!
                    fin = True
            if not fin:
                extract(p)
        
        def fillGaps(seqlist, lenlist):
            fill = [0 for i in range(0, len(seqlist))]
            for i in range(0, len(seqlist)-1):
                if seqlist[i] + lenlist[i] < seqlist[i+1]:
                    fill[i] = 1
            return fill
        
        play = False
        packetlist = []
        seqlist = []
        lenlist = []
        for p in self.cap:
            if p.haslayer(IP):
                if (str(p).find("PAUSE") != -1) and play:
                    VTLOG.debug("PAUSE found!")
                    break
                if not play:
                    play = self.__prepare(p)
                #Packets from server, with TCP layer. Avoid ACK's. Avoid RTSP packets
                elif play and (p[IP].src == self.conf['ip']) and p.haslayer(TCP) and (len(p) > 66) and (str(p).find("RTSP/1.0") == -1):
                    packetlist.append(p)
                    seqlist.append(p[TCP].seq)
                    lenlist.append(len(p[TCP].payload))
                    VTLOG.debug("TCP packet appended. Sequence: " + str(p[TCP].seq))
        seqlist, packetlist, lenlist = self.__bubbleSort(seqlist, packetlist, lenlist)
        VTLOG.debug("Sequence list sorted")
        #Locate packet losses
        fill = fillGaps(seqlist, lenlist)
        stream = ''
        for i, p in enumerate(packetlist):
            stream = ''.join([stream, str(p[TCP].payload)])
            #Mark ENDOFPACKET and save time and length
            stream = ''.join([stream, 'ENDOFPACKET'])
            stream = ''.join([stream, str(int(p.time * 1000000))])
            stream = ''.join([stream, 'ENDOFPACKET'])
            stream = ''.join([stream, str(p.len)])
            stream = ''.join([stream, 'ENDOFPACKET'])
            if fill[i]:
                #Mark PACKETLOSS
                VTLOG.debug("PACKETLOSS!")
                stream = ''.join([stream, 'PACKETLOSS'])
        VTLOG.debug("TCP payloads assembled")
        stream = RTSPi(stream)
        extract(stream)
    
    def __normalize(self):
        seq = self.sequences[0]
        time = self.times[0]
        timest = float(self.timestamps[0])
        for i in range(0, len(self.sequences)):
            self.sequences[i] = self.sequences[i] - seq
            self.times[i] = self.times[i] - time
            self.timestamps[i] = (float(self.timestamps[i]) - timest) / self.clock