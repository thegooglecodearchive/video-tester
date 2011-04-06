# coding=UTF8
## This file is part of VideoTester
## See http://video-tester.googlecode.com for more information
## Copyright 2011 Iñaki Úcar <i.ucar86@gmail.com>
## This program is published under a GPLv3 license

from config import VTLOG
from sys import exit

class VT:
    """
    Superclass that gathers several common functionalities shared by the client and the server.
    """
    def __init__(self):
        """
        **On init:** Parse the `video` section.
        
        .. warning::
            This section MUST be present in the default configuration file (see :const:`VideoTester.config.CONF`)
            and MUST contain the same videos at the client and the server.
        
        Raises:
            | `Except`: Bad configuration file or path.
        """
        from config import CONF
        try:
            #: List of ``(id, name)`` pairs for each available video.
            self.videos = self.parseConf(CONF, "video")
            if self.videos[0][0] != 'path':
                raise
            #: Path to the video directory.
            self.path = self.videos[0][1]
            self.videos.pop(0)
        except:
            VTLOG.error("Bad '" + CONF + "' file or path")
            exit()
    
    def run(self):
        """
        Do nothing.
        
        .. note::
            This method MUST be overwritten by the subclasses.
        """
        pass

    def parseConf(self, file, section):
        """
        Extract a section from a configuration file.
        
        Args:
            | `file` (string): Path to the configuration file.
            | `section` (string): Section to be extracted.
        
        Returns:
            | A list of ``(name, value)`` pairs for each option in the given section.
        """
        import ConfigParser
        config = ConfigParser.RawConfigParser()
        config.read(file)
        return config.items(section)

class Server(VT):
    """
    VT Server class.
    """
    def __init__(self):
        """
        **On init:** Some initialization code.
        """
        VT.__init__(self)
        from config import SERVERIP, SERVERPORT
        #: List of available videos (complete path).
        self.videos = [''.join([self.path, x[1]]) for x in self.videos]
        #: Dictionary of running RTSP servers.
        self.servers = dict()
        #: Next RTSP port (integer). It increases each time by one.
        self.port = SERVERPORT + 1
        self.__launch(SERVERIP, SERVERPORT)
    
    def __launch(self, ip, port):
        """
        Launch the XMLRPC server and offer the methods :meth:`VideoTester.core.Server.run` and :meth:`VideoTester.core.Server.stop`
        
        Args:
            | `ip` (string): The server IP address.
            | `port` (string): The XMLRPC listen port.
        """
        from SimpleXMLRPCServer import SimpleXMLRPCServer
        server = SimpleXMLRPCServer((ip, port), logRequests=False)
        server.register_function(self.run)
        server.register_function(self.stop)
        try:
            VTLOG.info('XMLRPC Server running at ' + ip + ':' + str(port))
            VTLOG.info('Use Control-C to exit')
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        
    def run(self, bitrate, framerate):
        """
        Run a subprocess for an RTSP server with a given bitrate and framerate (if not running)
        or add a client (if running).
        
        Args:
            | `bitrate` (string or integer): The bitrate (in kbps).
            | `framerate` (string or integer): The framerate (in fps).
        
        Returns:
            | The RTSP server port in integer format.
        
        Raises:
            | `OSError`: An error ocurred while running subprocess.
        """
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
            VTLOG.info("RTSP Server running!")
        VTLOG.info("PID: " + str(self.servers[key]['server'].pid) + ", " + key + " server, connected clients: " + str(self.servers[key]['clients']))
        return self.servers[key]['port']
    
    def stop(self, bitrate, framerate):
        """
        Stop an RTSP server with a given bitrate and framerate (if no remaining clients)
        or remove a client (if remaining clients).
        
        Args:
            | `bitrate` (string or integer): The bitrate (in kbps).
            | `framerate` (string or integer): The framerate (in fps).
        
        Returns:
            | True.
        """
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
        """
        Check that the :attr:`VideoTester.core.Server.port` is unused.
        
        Returns:
            | Boolean:
            |   True if port is unused.
            |   False if port is in use.
        """
        from socket import socket
        try:
            s = socket()
            s.bind(('localhost',self.port))
        except:
            return False
        s.close()
        return True

class Client(VT):
    """
    VT Client class.
    """
    def __init__(self, file, gui=False):
        """
        **On init:** Some initialization code.
        
        Args:
            | `file` (string or dictionary): Path to configuration file (string) or parsed configuration file (dictionary).
            | `gui` (boolean):
            |   True if :class:`VideoTester.core.Client` is called from GUI.
            |   False otherwise.
        
        .. warning::
            If ``gui == True``, `file` MUST be a dictionary. Otherwise, `file` MUST be a string.
        
        Raises:
            | `Exception`: Bad configuration file or path.
        """
        VT.__init__(self)
        from os.path import exists
        from config import TEMP, makeDir
        if gui:
            self.conf = file
        else:
            try:
                #: Dictionary of configuration options.
                self.conf = dict(self.parseConf(file, "client"))
            except:
                VTLOG.error("Bad configuration file or path")
                exit()
        #: Path to the selected video.
        self.video = ''.join([self.path, dict(self.videos)[self.conf['video']]])
        self.conf['tempdir'] = TEMP + self.conf['video'] + '_' + self.conf['codec'] + '_' + self.conf['bitrate'] + '_' + self.conf['framerate'] + '_' + self.conf['protocols'] + '/'
        makeDir(self.conf['tempdir'])
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
        #: Numerical prefix for temporary files.
        self.conf['num'] = num

    def run(self):
        """
        Run client and perform all the operations:
         * Connect to the server.
         * Receive video while sniffing packets.
         * Close connection.
         * Process data and extract information.
         * Run meters.
        
        Returns:
            | A list of measures (see [_]).
            | The path to the temporary directory plus files prefix: `<path-to-tempdir>/<prefix>`
        """
        VTLOG.info("Client running!")
        VTLOG.info("XMLRPC Server at " + self.conf['ip'] + ':' + self.conf['port'])
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
        child = Process(target=sniffer.run, args=(q,))
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
        videodata, size = gstreamer.reference()
        packetdata = sniffer.parsePkts()
        codecdata, rawdata = self.__loadData(videodata, size, self.conf['codec'])
        qosm = QoSmeter(self.conf['qos'], packetdata).run()
        bsm = BSmeter(self.conf['bs'], codecdata).run()
        vqm = VQmeter(self.conf['vq'], (rawdata, codecdata, packetdata)).run()
        self.__saveMeasures(qosm + bsm + vqm)
        VTLOG.info("Client stopped!")
        return qosm + bsm + vqm, self.conf['tempdir'] + self.conf['num']
    
    def __ping(self):
        """
        Ping to server (4 echoes).
        """
        from scapy.all import IP, ICMP, send
        from time import sleep
        sleep(0.5)
        VTLOG.info("Pinging...")
        for i in range(0, 4):
            send(IP(dst=self.conf['ip'])/ICMP(seq=i), verbose=False)
            sleep(0.5)
    
    def __loadData(self, videodata, size, codec):
        """
        Load raw video data and coded video data.
        
        Args:
            | `videodata` (see :attr:`VideoTester.gstreamer.Gstreamer.files`):
        
        Returns:
            | Coded video data object (see :class:`VideoTester.video.YUVvideo`).
            | Raw video data object (see :class:`VideoTester.video.CodedVideo`).
        """
        VTLOG.info("Loading videos...")
        from video import YUVvideo, CodedVideo
        codecdata = {}
        rawdata = {}
        for x in videodata.keys():
            if x != 'original':
                codecdata[x] = CodedVideo(videodata[x][0], codec)
            rawdata[x] = YUVvideo(videodata[x][1], size)
            VTLOG.info("+++")
        return codecdata, rawdata
    
    def __saveMeasures(self, measures):
        """
        Save measures to disc (with standard module :mod:`pickle`).
        
        Args:
            | `measures`: List of measures.
        """
        VTLOG.info("Saving measures...")
        from pickle import dump
        for measure in measures:
            f = open(self.conf['tempdir'] + self.conf['num'] + '_' + measure['name'] + '.pkl', "wb")
            dump(measure, f)
            f.close()