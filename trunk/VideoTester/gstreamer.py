# coding=UTF8
## This file is part of VideoTester
## See http://video-tester.googlecode.com for more information
## Copyright 2011 Iñaki Úcar <i.ucar86@gmail.com>
## This program is published under a GPLv3 license

from gobject import MainLoop
import pygst
pygst.require("0.10")
from gst import parse_launch, MESSAGE_EOS, MESSAGE_ERROR, STATE_PAUSED, STATE_READY, STATE_NULL, STATE_PLAYING
from time import sleep
from config import VTLOG
from pickle import dump

class Gstreamer:
    def __init__(self, conf, video):
        self.conf = conf
        self.video = video
        self.size = None
        self.files = {'original':[], 'coded':[], 'received':[]}
        self.pipeline = None
        self.loop = None
        self.uri = 'rtsp://' + self.conf['ip'] + ':' + self.conf['rtspport'] + '/' + self.conf['video'] + '.' + self.conf['codec']
        if self.conf['codec'] == "h263":
            self.encoder = "ffenc_h263"
            self.depay = "rtph263depay"
            self.bitrate = self.conf['bitrate'] + '000'
            self.add = ''
        elif self.conf['codec'] == "h264":
            self.encoder = "x264enc"
            self.depay = "rtph264depay"
            self.bitrate = self.conf['bitrate']
            self.add = ''
        elif self.conf['codec'] == "mpeg4":
            self.encoder = "ffenc_mpeg4"
            self.depay = "rtpmp4vdepay"
            self.bitrate = self.conf['bitrate'] + '000'
            self.add = ''
        elif self.conf['codec'] == "theora":
            self.encoder = "theoraenc"
            self.depay = "rtptheoradepay ! theoraparse"
            self.bitrate = self.conf['bitrate']
            self.add = ' ! matroskamux'
    
    def __events(self, bus, msg):
        t = msg.type
        if t == MESSAGE_EOS:
            self.pipeline.set_state(STATE_PAUSED)
            sleep(0.5)
            self.pipeline.set_state(STATE_READY)
            self.pipeline.set_state(STATE_NULL)
            VTLOG.debug("GStreamer: MESSAGE_EOS received")
            self.loop.quit()
        elif t == MESSAGE_ERROR:
            self.pipeline.set_state(STATE_PAUSED)
            sleep(0.5)
            self.pipeline.set_state(STATE_READY)
            self.pipeline.set_state(STATE_NULL)
            e, d = msg.parse_error()
            VTLOG.error("GStreamer: MESSAGE_ERROR received")
            VTLOG.error(e)
            self.loop.quit()
        return True
    
    def __play(self):
        self.pipeline.get_bus().add_watch(self.__events)
        self.pipeline.set_state(STATE_PLAYING)
        self.loop = MainLoop()
        self.loop.run()
        VTLOG.debug("GStreamer: Loop stopped")
    
    def receiver(self):
        VTLOG.info("Starting GStreamer receiver...")
        self.pipeline = parse_launch('rtspsrc name=source ! tee name=t ! queue ! ' + self.depay + self.add + ' ! filesink name=sink1 t. ! queue \
                ! decodebin ! videorate skip-to-first=True ! video/x-raw-yuv,framerate=' + self.conf['framerate'] + '/1 ! filesink name=sink2')
        source = self.pipeline.get_by_name('source')
        sink1 = self.pipeline.get_by_name('sink1')
        sink2 = self.pipeline.get_by_name('sink2')
        source.props.location = self.uri
        source.props.protocols = self.conf['protocols']
        location = self.conf['tempdir'] + self.conf['num'] + '.' + self.conf['codec']
        self.files['received'].append(location)
        sink1.props.location = location
        location = self.conf['tempdir'] + self.conf['num'] + '.yuv'
        self.files['received'].append(location)
        sink2.props.location = location
        pad = sink2.get_pad("sink")
        pad.connect("notify::caps", self.__notifyCaps)
        self.__play()
        VTLOG.info("GStreamer receiver stopped")
    
    def reference(self):
        VTLOG.info("Making reference...")
        self.pipeline = parse_launch('filesrc name=source ! decodebin ! videorate ! video/x-raw-yuv,framerate=' + self.conf['framerate'] + '/1  ! filesink name=sink1')
        source = self.pipeline.get_by_name('source')
        sink1 = self.pipeline.get_by_name('sink1')
        location = self.video
        self.files['original'].append(location)
        source.props.location = location
        location = self.conf['tempdir'] + self.conf['num'] + '_ref_original.yuv'
        self.files['original'].append(location)
        sink1.props.location = location
        self.__play()
        self.pipeline = parse_launch('filesrc name=source ! decodebin ! videorate ! video/x-raw-yuv,framerate=' + self.conf['framerate'] + '/1  ! ' + self.encoder + ' bitrate=' + self.bitrate \
                + ' ! tee name=t ! queue' + self.add + ' ! filesink name=sink2 t. ! queue ! decodebin ! filesink name=sink3')
        source = self.pipeline.get_by_name('source')
        sink2 = self.pipeline.get_by_name('sink2')
        sink3 = self.pipeline.get_by_name('sink3')
        location = self.video
        source.props.location = location
        location = self.conf['tempdir'] + self.conf['num'] + '_ref.' + self.conf['codec']
        self.files['coded'].append(location)
        sink2.props.location = location
        location = self.conf['tempdir'] + self.conf['num'] + '_ref.yuv'
        self.files['coded'].append(location)
        sink3.props.location = location
        self.__play()
        VTLOG.info("Reference made")
        return self.files, self.size
    
    def __notifyCaps(self, pad, args):
        caps = pad.get_negotiated_caps()
        if caps:
            caps = caps.to_string()
            aux = caps.split(', ')
            for x in aux:
                if x.find('width') != -1:
                    width = int(x[11:len(x)])
                elif x.find('height') != -1:
                    height = int(x[12:len(x)])
            self.size = (width, height)
            f = open(self.conf['tempdir'] + self.conf['num'] + '_caps.txt', "wb")
            f.write(caps)
            f.close()