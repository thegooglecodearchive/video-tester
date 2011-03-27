# coding=UTF8
## This file is part of VideoTester
## See http://video-tester.googlecode.com for more information
## Copyright 2011 Iñaki Úcar <i.ucar86@gmail.com>
## This program is published under a GPLv3 license

from measures import Meter, Measure
from VideoTester.config import VTLOG

class QoSmeter(Meter):
    def __init__(self, selected, data):
        Meter.__init__(self)
        VTLOG.info("Starting QoSmeter...")
        if 'latency' in selected:
            self.measures.append(Latency(data))
        if 'delta' in selected:
            self.measures.append(Delta(data))
        if 'jitter' in selected:
            self.measures.append(Jitter(data))
        if 'skew' in selected:
            self.measures.append(Skew(data))
        if 'bandwidth' in selected:
            self.measures.append(Bandwidth(data))
        if 'plr' in selected:
            self.measures.append(PacketLossRate(data))
        if 'pld' in selected:
            self.measures.append(PacketLossDist(data))

class QoSmeasure(Measure):
    def __init__(self, (lengths, times, sequences, timestamps, ping)):
        Measure.__init__(self)
        self.lengths = lengths
        self.times = times
        self.sequences = sequences
        self.timestamps = timestamps
        self.ping = ping

class Latency(QoSmeasure):
    def __init__(self, data):
        QoSmeasure.__init__(self, data)
        self.measure['name'] = 'Latency'
        self.measure['units'] = 'ms'
        self.measure['type'] = 'value'
    
    def calculate(self):
        sum = 0
        count = 0
        for i in range(0, 4):
            if len(self.ping[i]) == 2:
                sum = sum + (self.ping[i][0] - self.ping[i][8]) * 500
                count = count + 1
        self.measure['value'] = sum / count
        return self.measure

class Delta(QoSmeasure):
    def __init__(self, data):
        QoSmeasure.__init__(self, data)
        self.measure['name'] = 'Delta'
        self.measure['units'] = ['RTP packet', 'ms']
        self.measure['type'] = 'plot'
    
    def calculate(self):
        x = self.sequences
        y = [0 for i in range(0, len(self.times))]
        for i in range(1, len(self.times)):
            y[i] = (self.times[i] - self.times[i-1]) * 1000
        self.graph(x, y)
        return self.measure

class Jitter(QoSmeasure):
    def __init__(self, data):
        QoSmeasure.__init__(self, data)
        self.measure['name'] = 'Jitter'
        self.measure['units'] = ['RTP packet', 'ms']
        self.measure['type'] = 'plot'
    
    def calculate(self):
        #ms (see RFC 3550)
        x = self.sequences
        y = [0 for i in range(0, len(self.times))]
        for i in range(1, len(self.times)):
            d = ((self.times[i] - self.timestamps[i]) - (self.times[i-1] - self.timestamps[i-1])) * 1000
            y[i] = y[i-1] + (abs(d) - y[i-1]) / 16
        self.graph(x, y)
        return self.measure

class Skew(QoSmeasure):
    def __init__(self, data):
        QoSmeasure.__init__(self, data)
        self.measure['name'] = 'Skew'
        self.measure['units'] = ['RTP packet', 'ms']
        self.measure['type'] = 'plot'
    
    def calculate(self):
        x = self.sequences
        y = [0 for i in range(0, len(self.times))]
        for i in range(1, len(self.times)):
            y[i] = (self.timestamps[i] - self.times[i]) * 1000
        self.graph(x, y)
        return self.measure

class Bandwidth(QoSmeasure):
    def __init__(self, data):
        QoSmeasure.__init__(self, data)
        self.measure['name'] = 'Bandwidth'
        self.measure['units'] = ['time (s)', 'kbps']
        self.measure['type'] = 'plot'
    
    def calculate(self):
        x = self.times
        y = [0 for i in range(0, len(x))]
        for i in range(1, len(x)):
            if x[i] == x[i-1]:
                y[i] = -1
        supr = True
        while supr:
            try:
                x.pop(y.index(-1))
                y.pop(y.index(-1))
                self.lengths.pop(y.index(-1))
            except:
                supr = False
        for i in range(1, len(x)):
            length = 0
            j = i
            while x[j] + 1 > x[i] and j >= 0:
                length = length + self.lengths[i] * 8 / 1000
                j = j - 1
            y[i] = length
        self.graph(x, y)
        return self.measure

class PacketLossRate(QoSmeasure):
    def __init__(self, data):
        QoSmeasure.__init__(self, data)
        self.measure['name'] = 'PLR'
        self.measure['units'] = 'rate'
        self.measure['type'] = 'value'
    
    def calculate(self):
        loss = 0
        for i in range(1, len(self.sequences)):
            loss = loss + self.sequences[i] - self.sequences[i-1] - 1
        rate = float(loss) / float(self.sequences[-1] + 1)
        self.measure['value'] = rate
        return self.measure

class PacketLossDist(QoSmeasure):
    def __init__(self, data):
        QoSmeasure.__init__(self, data)
        self.measure['name'] = 'PLD'
        self.measure['units'] = ['time (s)', 'Packet Loss Rate']
        self.measure['type'] = 'bar'
        self.measure['width'] = 1 #seconds
    
    def calculate(self):
        edge = self.measure['width']
        x = []
        y = []
        i = 1
        j = 1
        count = 1
        while i < len(self.times):
            x.append((j-1) * self.measure['width'])
            loss = 0
            while i < len(self.times) and self.times[i] < edge:
                count = count + 1
                loss = loss + self.sequences[i] - self.sequences[i-1] - 1
                i = i + 1
            y.append(float(loss) / count)
            count = 0
            edge = edge + self.measure['width']
            j = j + 1
        self.graph(x, y)
        return self.measure