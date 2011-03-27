# coding=UTF8
## This file is part of VideoTester
## See http://video-tester.googlecode.com for more information
## Copyright 2011 Iñaki Úcar <i.ucar86@gmail.com>
## This program is published under a GPLv3 license

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

class CodedVideo:
    def __init__(self, file, codec):
        self.f = fromfile(file, dtype=uint8)
        self.frames = {'types':[], 'lengths':[]}
        if codec == 'h263':
            self.__readH263()
        elif codec == 'h264':
            self.__readH264()
        elif codec == 'mpeg4':
            self.__readMPEG4()
        elif codec == 'theora':
            self.__readTheora()
    
    def __readH263(self):
        PSC = array([0x00, 0x00, 0x80], dtype=uint8)
        mask = array([0xff, 0xff, 0xfc], dtype=uint8)
        first = -1
        i = 0
        while i < len(self.f)-3:
            if all((self.f[i:i+3] & mask) == PSC):
                if (i != 0) and (first > -1):
                    self.frames['lengths'].append(i-first)
                first = i
                i += 4
                if (self.f[i] & 0x02) == 0:
                    self.frames['types'].append('I')
                else:
                    self.frames['types'].append('P')
            i += 1
    
    def __readH264(self):
        def getType(byte):
            comp = byte & 0x7f
            if comp >= 0x40:
                codeNum = 0
            elif comp >= 0x30:
                codeNum = 2
            elif comp >= 0x20:
                codeNum = 1
            elif comp >= 0x1c:
                codeNum = 6
            elif comp >= 0x18:
                codeNum = 5
            elif comp >= 0x14:
                codeNum = 4
            elif comp >= 0x10:
                codeNum = 3
            elif comp >= 0x0a:
                codeNum = 9
            elif comp >= 0x09:
                codeNum = 8
            elif comp >= 0x08:
                codeNum = 7
            if codeNum == 2 or codeNum == 7:
                type = 'I'
            elif codeNum == 0 or codeNum == 5:
                type = 'P'
            elif codeNum == 1 or codeNum == 6:
                type = 'B'
            elif codeNum == 3 or codeNum == 8:
                type = 'SP'
            elif codeNum == 4 or codeNum == 9:
                type = 'SI'
            return type
        
        SC = array([0x00, 0x00, 0x00, 0x01], dtype=uint8)
        SCmask = array([0xff, 0xff, 0xff, 0xff], dtype=uint8)
        typeI = 0x05
        typePB = 0x01
        typemask = 0x1f
        flag = True
        first = 0
        i = 0
        while i < len(self.f)-4:
            if all((self.f[i:i+4] & SCmask) == SC):
                if flag:
                    if i != 0:
                        self.frames['lengths'].append(i-first)
                    first = i
                    flag = False
                i += 4
                if ((self.f[i] & typemask) == typeI) or ((self.f[i] & typemask) == typePB):
                    flag = True
                    i += 1
                    self.frames['types'].append(getType(self.f[i:i+1]))
            i += 1
    
    def __readMPEG4(self):
        SC = array([0x00, 0x00, 0x01, 0xb6], dtype=uint8)
        mask = array([0xff, 0xff, 0xff, 0xff], dtype=uint8)
        first = -1
        i = 0
        while i < len(self.f)-4:
            if all((self.f[i:i+4] & mask) == SC):
                if (i != 0) and (first > -1):
                    self.frames['lengths'].append(i-first)
                first = i
                i += 4
                comp = self.f[i] & 0xc0
                if comp == 0x00:
                    self.frames['types'].append('I')
                elif comp == 0x40:
                    self.frames['types'].append('P')
                elif comp == 0x80:
                    self.frames['types'].append('B')
                elif comp == 0xc0:
                    self.frames['types'].append('S')
            i += 1
    
    def __readTheora(self):
        pass
        