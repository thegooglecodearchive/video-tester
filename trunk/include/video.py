# coding=UTF8

from numpy import *

class YUVvideo:
    def __init__(self, file, framesize, format='I420'):
        self.framesize = framesize
        self.frames = None
        self.video = {'Y':[], 'U':[], 'V':[]}
        if format == 'I420':
            self.__readI420(file, framesize)
    
    def __readI420(self, file, (width, height)):
        yblock = width * height
        uvblock = width * height / 4
        frame = yblock + 2 * uvblock
        f = open(file, "rb")
        raw = f.read()
        f.close()
        self.frames = len(raw) / frame
        y = 0
        u = y + yblock
        v = y + yblock + uvblock
        count = 1
        while y < len(raw):
            self.video['Y'].append(frombuffer(raw[y:y+yblock], dtype=uint8).reshape(height, width))
            y += frame
            self.video['U'].append(frombuffer(raw[u:u+uvblock], dtype=uint8).reshape(height/2, width/2))
            u += frame
            self.video['V'].append(frombuffer(raw[v:v+uvblock], dtype=uint8).reshape(height/2, width/2))
            v += frame