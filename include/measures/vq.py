# coding=UTF8

from measures import Meter, Measure
from qos import QoSmeter
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
##        if 'ssim' in selected:
##            self.measures.append(SSIM(data))

class VQmeasure(Measure):
    def __init__(self, (videodata, packetdata)):
        Measure.__init__(self)
        self.packetdata = packetdata
        self.yuv = videodata['received'][1]
        self.yuvref = videodata['original'][1]
    
    def getQoSm(self, measure):
        return QoSmeter(measure, self.packetdata).run()

class PSNR(VQmeasure):
    def __init__(self, data, component='Y'):
        VQmeasure.__init__(self, data)
        self.cmp = component
        self.measure['name'] = self.cmp + '-PSNR'
        self.measure['units'] = ['frame', 'dB']
        self.measure['type'] = 'plot'
    
    def calculate(self):
        L = 255
        width = self.yuv.video[self.cmp][0].shape[0]
        height = self.yuv.video[self.cmp][0].shape[1]
        fin = min(self.yuv.frames, self.yuvref.frames)
        x = range(0, fin)
        y = []
        for i in x:
            sum = (self.yuv.video[self.cmp][i].astype(int) - self.yuvref.video[self.cmp][i].astype(int))**2
            mse = sum.sum() / width / height
            if mse != 0:
                y.append(20 * math.log(L / math.sqrt(mse), 10))
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

class SSIM(VQmeasure):
    def __init__(self, data):
        VQmeasure.__init__(self, data)
        self.measure['name'] = 'SSIM'
        self.measure['units'] = ['frame', 'SSIM index']
        self.measure['type'] = 'plot'
    
    def calculate(self):
        L = 255
        c1 = (0.01 * L)**2
        c2 = (0.03 * L)**2
        window = 11
        step = 11
        width = self.yuv.video['Y'][0].shape[0]
        height = self.yuv.video['Y'][0].shape[1]
        fin = min(self.yuv.frames, self.yuvref.frames)
        x = range(0, fin)
        y = []
        for k in x:
            ssim = []
            for i in range(window, width, step):
                for j in range(window, height, step):
                    M1 = self.yuv.video['Y'][k][i-window:i, j-window:j].astype(int)
                    M2 = self.yuvref.video['Y'][k][i-window:i, j-window:j].astype(int)
                    mu1 = M1.mean()
                    mu2 = M2.mean()
                    var1 = ((M1 - mu1)**2).mean()
                    var2 = ((M2 - mu2)**2).mean()
                    ssim.append(((2*mu1*mu2 + c1) * (2*math.sqrt(var1)*math.sqrt(var2) + c2) / ((mu1**2 + mu2**2 + c1) * (var1 + var2 + c2))))
            sum = 0
            for i in ssim:
                sum = sum + i
            y.append(sum / len(ssim))
        self.graph(x, y)
        return self.measure