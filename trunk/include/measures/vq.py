# coding=UTF8

from measures import Meter, Measure
from include.config import vtLog
import math

class VQmeter(Meter):
    def __init__(self, selected, data):
        Meter.__init__(self)
        vtLog.info("Starting VQmeter...")
        if 'ypsnr' in selected:
            self.measures.append(PSNR(data))
        if 'upsnr' in selected:
            self.measures.append(UPSNR(data))
        if 'vpsnr' in selected:
            self.measures.append(VPSNR(data))

class VQmeasure(Measure):
    def __init__(self, files):
        Measure.__init__(self)
        self.yuv = files['received'][1]
        self.yuvref = files['original'][1]

class PSNR(VQmeasure):
    def __init__(self, data, component='Y'):
        VQmeasure.__init__(self, data)
        self.cmp = component
        self.measure['name'] = self.cmp + '-PSNR'
        self.measure['units'] = ['frame', 'dB']
        self.measure['type'] = 'plot'
    
    def calculate(self):
        width = self.yuv.video[self.cmp][0].shape[0]
        height = self.yuv.video[self.cmp][0].shape[1]
        fin = min(self.yuv.frames, self.yuvref.frames)
        x = range(0, fin)
        y = []
        for i in range(0, fin):
            sum = (self.yuv.video[self.cmp][i].astype(int) - self.yuvref.video[self.cmp][i].astype(int))**2
            mse = sum.sum() / width / height
            if mse != 0:
                y.append(20 * math.log(255 / math.sqrt(mse), 10))
            else:
                y.append(100)
        self.graph(x, y)
        return self.measure

class UPSNR(PSNR):
    def __init__(self, data):
        PSNR.__init__(self, data, 'U')

class VPSNR(PSNR):
    def __init__(self, data):
        PSNR.__init__(self, data, 'V')
