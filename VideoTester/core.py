# coding=UTF8

from config import VTLOG
from sys import exit

class VT:
    def __init__(self):
        from config import CONF
        try:
            self.videos = self.parseConf(CONF, "video")
            if self.videos[0][0] != 'path':
                raise
            self.path = self.videos[0][1]
            self.videos.pop(0)
        except:
            VTLOG.error("Bad '" + CONF + "' file")
            exit()

    def parseConf(self, file, section):
        import ConfigParser
        config = ConfigParser.RawConfigParser()
        config.read(file)
        return config.items(section)
    
    def run(self):
        pass

class Server(VT):
    def __init__(self):
        VT.__init__(self)
        from config import SERVERPORT
        self.videos = [''.join([self.path, x[1]]) for x in self.videos]
        self.servers = dict()
        self.port = SERVERPORT + 1
        
    def run(self, bitrate, framerate):
        from subprocess import Popen, PIPE
        from config import SERVERBIN
        key = str(bitrate) + ' kbps - ' + str(framerate) + ' fps'
        if key in self.servers:
            self.servers[key]['clients'] = self.servers[key]['clients'] + 1
        else:
            self.servers[key] = dict()
            while not self.__freePort():
                self.port = self.port + 1
            command = [SERVERBIN, "-p", str(self.port), "-f", str(framerate), "-b", str(bitrate), "-v"]
            command.extend(self.videos)
            try:
                self.servers[key]['server'] = Popen(command, stdout=PIPE)
            except OSError, e:
                VTLOG.error(e)
                exit()
            self.servers[key]['port'] = self.port
            self.servers[key]['clients'] = 1
            VTLOG.info("Server running!")
        VTLOG.info("PID: " + str(self.servers[key]['server'].pid) + ", " + key + " server, connected clients: " + str(self.servers[key]['clients']))
        return self.servers[key]['port']
    
    def stop(self, bitrate, framerate):
        key = str(bitrate) + ' kbps - ' + str(framerate) + ' fps'
        self.servers[key]['clients'] = self.servers[key]['clients'] - 1
        if self.servers[key]['clients'] == 0:
            self.servers[key]['server'].terminate()
            self.servers[key]['server'].wait()
            VTLOG.info(key + " server: last client disconnected and server stopped")
            self.servers.pop(key)
        else:
            VTLOG.info(key + " server: client disconnected. Remaining: " + str(self.servers[key]['clients']))
        return True
    
    def __freePort(self):
        from socket import socket
        try:
            s = socket()
            s.bind(('localhost',self.port))
        except:
            return False
        s.close()
        return True

class Client(VT):
    def __init__(self, file, gui=False):
        VT.__init__(self)
        from os.path import exists
        from config import TEMP, createDir
        self.gui = gui
        if self.gui:
            self.conf = file
        else:
            try:
                self.conf = dict(self.parseConf(file, "client"))
            except:
                VTLOG.error("Bad configuration file")
                exit()
        self.video = ''.join([self.path, dict(self.videos)[self.conf['video']]])
        self.conf['tempdir'] = TEMP + self.conf['video'] + '_' + self.conf['codec'] + '_' + self.conf['bitrate'] + '_' + self.conf['framerate'] + '_' + self.conf['protocols'] + '/'
        createDir(self.conf['tempdir'])
        i , j = 0, True
        while j and i < 100:
            if i < 10:
                num = '0' + str(i)
            else:
                num = str(i)
            i = i + 1
            j = exists(self.conf['tempdir'] + num + '.yuv')
        if j:
            VTLOG.error("The TEMP directory is full")
            exit()
        self.conf['num'] = num

    def run(self):
        VTLOG.info("Client running!")
        VTLOG.info("Server at " + self.conf['ip'])
        VTLOG.info("Evaluating: " + self.conf['video'] + " + " + self.conf['codec'] + " at " + self.conf['bitrate'] + " kbps and " + self.conf['framerate'] + " fps under " + self.conf['protocols'])
        from xmlrpclib import ServerProxy
        from scapy.all import rdpcap
        from multiprocessing import Process, Queue
        from gstreamer import Gstreamer
        from sniffer import Sniffer
        from measures.qos import QoSmeter
        from measures.bs import BSmeter
        from measures.vq import VQmeter
        try:
            server = ServerProxy('http://' + self.conf['ip'] + ':' + self.conf['port'])
            self.conf['rtspport'] = str(server.run(self.conf['bitrate'], self.conf['framerate']))
        except:
            VTLOG.error("Bad IP or port")
            exit()
        sniffer = Sniffer(self.conf)
        gstreamer = Gstreamer(self.conf, self.video)
        q = Queue()
        child = Process(target=sniffer.run, args=(q, self.gui))
        try:
            child.start()
            self.__ping()
            gstreamer.receiver()
            sniffer.cap = rdpcap(q.get())
            child.join()
        except KeyboardInterrupt:
            VTLOG.warning("Keyboard interrupt!")
            server.stop(self.conf['bitrate'], self.conf['framerate'])
            child.terminate()
            child.join()
            exit()
        server.stop(self.conf['bitrate'], self.conf['framerate'])
        self.videodata, size = gstreamer.reference()
        self.packetdata = sniffer.parsePkts()
        self.codecdata, self.rawdata = self.__loadData(size, self.conf['codec'])
        qosm = QoSmeter(self.conf['qos'], self.packetdata).run()
        bsm = BSmeter(self.conf['bs'], self.codecdata).run()
        vqm = VQmeter(self.conf['vq'], (self.rawdata, self.codecdata, self.packetdata)).run()
        self.__saveMeasures(qosm + bsm + vqm)
        VTLOG.info("Client stopped!")
        return qosm + bsm + vqm, self.conf['tempdir'] + self.conf['num']
    
    def __ping(self):
        from scapy.all import IP, ICMP, send
        from time import sleep
        sleep(0.5)
        VTLOG.info("Pinging...")
        for i in range(0, 4):
            send(IP(dst=self.conf['ip'])/ICMP(seq=i), verbose=False)
            sleep(0.5)
    
    def __loadData(self, size, codec):
        VTLOG.info("Loading videos...")
        from video import YUVvideo, CodedVideo
        codecdata = {}
        rawdata = {}
        for x in self.videodata.keys():
            if x != 'original':
                codecdata[x] = CodedVideo(self.videodata[x][0], codec)
            rawdata[x] = YUVvideo(self.videodata[x][1], size)
            VTLOG.info("+++")
        return codecdata, rawdata
    
    def __saveMeasures(self, measures):
        VTLOG.info("Saving measures...")
        from pickle import dump
        for measure in measures:
            f = open(self.conf['tempdir'] + self.conf['num'] + '_' + measure['name'] + '.pkl', "wb")
            dump(measure, f)
            f.close()