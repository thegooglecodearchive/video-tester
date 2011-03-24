# coding=UTF8

from measures import Meter, Measure
from qos import QoSmeter
from include.config import vtLog
from numpy import *
import math
import cv

class VQmeter(Meter):
    def __init__(self, selected, data):
        Meter.__init__(self)
        vtLog.info("Starting VQmeter...")
        if 'streameye' in selected:
            self.measures.append(StreamEye(data))
        if 'refstreameye' in selected:
            self.measures.append(RefStreamEye(data))
        if 'gop' in selected:
            self.measures.append(GOP(data))
        if 'iflr' in selected:
            self.measures.append(IFrameLossRate(data))
        if 'ypsnr' in selected:
            self.measures.append(PSNR(data))
        if 'upsnr' in selected:
            self.measures.append(UPSNR(data))
        if 'vpsnr' in selected:
            self.measures.append(VPSNR(data))
        if 'ssim' in selected:
            self.measures.append(SSIM(data))

class VQmeasure(Measure):
    def __init__(self, (videodata, packetdata)):
        Measure.__init__(self)
        self.packetdata = packetdata
        self.coded = videodata['received'][0]
        self.codedref = videodata['coded'][0]
        self.yuv = videodata['received'][1]
        self.yuvref = videodata['original'][1]
    
    def getQoSm(self, measure):
        return QoSmeter(measure, self.packetdata).run()

class StreamEye(VQmeasure):
    def __init__(self, data, video=''):
        VQmeasure.__init__(self, data)
        if video == 'ref':
            self.v = self.codedref
        elif video == '':
            self.v = self.coded
        self.measure['name'] = video + 'StreamEye'
        self.measure['units'] = ['frame', 'bytes']
        self.measure['type'] = 'videoframes'
    
    def calculate(self):
        x = range(len(self.v.frames['lengths']))
        Iframes = [0 for i in x]
        Pframes = [0 for i in x]
        Bframes = [0 for i in x]
        for i in x:
            type = self.v.frames['types'][i]
            if type == 'I':
                Iframes[i] = self.v.frames['lengths'][i]
            elif type == 'P':
                Pframes[i] = self.v.frames['lengths'][i]
            elif type == 'B':
                Bframes[i] = self.v.frames['lengths'][i]
        y = {'I':Iframes, 'P':Pframes, 'B':Bframes}
        self.measure['axes'] = [x, y]
        return self.measure

class RefStreamEye(StreamEye):
    def __init__(self, data):
        StreamEye.__init__(self, data, 'ref')

class GOP(VQmeasure):
    def __init__(self, data):
        VQmeasure.__init__(self, data)
        self.measure['name'] = 'GOP'
        self.measure['units'] = 'GOP size'
        self.measure['type'] = 'value'
    
    def calculate(self):
        gops = []
        gop = 0
        for i in range(len(self.coded.frames['types'])):
            gop += 1
            if self.coded.frames['types'][i] == 'I':
                if i != 0:
                    gops.append(gop)
                gop = 0
        gops.append(gop)
        gops = array(gops, dtype=float)
        loss = []
        lim1 = mean(gops) - std(gops)/2
        lim2 = mean(gops) + std(gops)/2
        for i in range(len(gops)):
            if (gops[i] < lim1) or (gops[i] > lim2):
                loss.append(i)
        gops = delete(gops, loss)
        self.measure['value'] = int(round(mean(gops)))
        return self.measure

class IFrameLossRate(VQmeasure):
    def __init__(self, data):
        VQmeasure.__init__(self, data)
        self.measure['name'] = 'IFLR'
        self.measure['units'] = 'rate'
        self.measure['type'] = 'value'
    
    def calculate(self):
        count = 0
        gops = []
        gop = 0
        for i in range(len(self.coded.frames['types'])):
            gop += 1
            if self.coded.frames['types'][i] == 'I':
                count += 1
                if i != 0:
                    gops.append(gop)
                gop = 0
        gops.append(gop)
        gops = array(gops, dtype=float)
        loss = []
        lim = mean(gops) + std(gops)
        for i in range(len(gops)):
            if gops[i] > lim:
                loss.append(i)
        rate = float(len(loss)) / float(count + len(loss))
        self.measure['value'] = rate
        return self.measure

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
    
    def __array2cv(self, a):
        dtype2depth = {
            'uint8':   cv.IPL_DEPTH_8U,
            'int8':    cv.IPL_DEPTH_8S,
            'uint16':  cv.IPL_DEPTH_16U,
            'int16':   cv.IPL_DEPTH_16S,
            'int32':   cv.IPL_DEPTH_32S,
            'float32': cv.IPL_DEPTH_32F,
            'float64': cv.IPL_DEPTH_64F,
        }
        try:
            nChannels = a.shape[2]
        except:
            nChannels = 1
        cv_im = cv.CreateImageHeader((a.shape[1],a.shape[0]), dtype2depth[str(a.dtype)], nChannels)
        cv.SetData(cv_im, a.tostring(), a.dtype.itemsize*nChannels*a.shape[1])
        return cv_im
    
    def __SSIM(self, frame1, frame2):
        """
            The equivalent of Zhou Wang's SSIM matlab code using OpenCV.
            from http://www.cns.nyu.edu/~zwang/files/research/ssim/index.html
            The measure is described in :
            "Image quality assessment: From error measurement to structural similarity"
            C++ code by Rabah Mehdi. http://mehdi.rabah.free.fr/SSIM
            
            C++ to Python translation and adaptation by Iñaki Úcar
        """
        C1 = 6.5025
        C2 = 58.5225
        img1_temp = self.__array2cv(frame1)
        img2_temp = self.__array2cv(frame2)
        nChan = img1_temp.nChannels
        d = cv.IPL_DEPTH_32F
        size = img1_temp.width, img1_temp.height
        img1 = cv.CreateImage(size, d, nChan)
        img2 = cv.CreateImage(size, d, nChan)
        cv.Convert(img1_temp, img1)
        cv.Convert(img2_temp, img2)
        img1_sq = cv.CreateImage(size, d, nChan)
        img2_sq = cv.CreateImage(size, d, nChan)
        img1_img2 = cv.CreateImage(size, d, nChan)
        cv.Pow(img1, img1_sq, 2)
        cv.Pow(img2, img2_sq, 2)
        cv.Mul(img1, img2, img1_img2, 1)
        mu1 = cv.CreateImage(size, d, nChan)
        mu2 = cv.CreateImage(size, d, nChan)
        mu1_sq = cv.CreateImage(size, d, nChan)
        mu2_sq = cv.CreateImage(size, d, nChan)
        mu1_mu2 = cv.CreateImage(size, d, nChan)
        sigma1_sq = cv.CreateImage(size, d, nChan)
        sigma2_sq = cv.CreateImage(size, d, nChan)
        sigma12 = cv.CreateImage(size, d, nChan)
        temp1 = cv.CreateImage(size, d, nChan)
        temp2 = cv.CreateImage(size, d, nChan)
        temp3 = cv.CreateImage(size, d, nChan)
        ssim_map = cv.CreateImage(size, d, nChan)
        #/*************************** END INITS **********************************/
        #// PRELIMINARY COMPUTING
        cv.Smooth(img1, mu1, cv.CV_GAUSSIAN, 11, 11, 1.5)
        cv.Smooth(img2, mu2, cv.CV_GAUSSIAN, 11, 11, 1.5)
        cv.Pow(mu1, mu1_sq, 2)
        cv.Pow(mu2, mu2_sq, 2)
        cv.Mul(mu1, mu2, mu1_mu2, 1)
        cv.Smooth(img1_sq, sigma1_sq, cv.CV_GAUSSIAN, 11, 11, 1.5)
        cv.AddWeighted(sigma1_sq, 1, mu1_sq, -1, 0, sigma1_sq)
        cv.Smooth(img2_sq, sigma2_sq, cv.CV_GAUSSIAN, 11, 11, 1.5)
        cv.AddWeighted(sigma2_sq, 1, mu2_sq, -1, 0, sigma2_sq)
        cv.Smooth(img1_img2, sigma12, cv.CV_GAUSSIAN, 11, 11, 1.5)
        cv.AddWeighted(sigma12, 1, mu1_mu2, -1, 0, sigma12)
        #//////////////////////////////////////////////////////////////////////////
        #// FORMULA
        #// (2*mu1_mu2 + C1)
        cv.Scale(mu1_mu2, temp1, 2)
        cv.AddS(temp1, C1, temp1)
        #// (2*sigma12 + C2)
        cv.Scale(sigma12, temp2, 2)
        cv.AddS(temp2, C2, temp2)
        #// ((2*mu1_mu2 + C1).*(2*sigma12 + C2))
        cv.Mul(temp1, temp2, temp3, 1)
        #// (mu1_sq + mu2_sq + C1)
        cv.Add(mu1_sq, mu2_sq, temp1)
        cv.AddS(temp1, C1, temp1)
        #// (sigma1_sq + sigma2_sq + C2)
        cv.Add(sigma1_sq, sigma2_sq, temp2)
        cv.AddS(temp2, C2, temp2)
        #// ((mu1_sq + mu2_sq + C1).*(sigma1_sq + sigma2_sq + C2))
        cv.Mul(temp1, temp2, temp1, 1)
        #// ((2*mu1_mu2 + C1).*(2*sigma12 + C2))./((mu1_sq + mu2_sq + C1).*(sigma1_sq + sigma2_sq + C2))
        cv.Div(temp3, temp1, ssim_map, 1)
        index_scalar = cv.Avg(ssim_map)
        #// through observation, there is approximately 
        #// 1% error max with the original matlab program
        return index_scalar[0]
    
    def calculate(self):
        fin = min(self.yuv.frames, self.yuvref.frames)
        x = range(0, fin)
        y = []
        for i in x:
            y.append(self.__SSIM(self.yuv.video['Y'][i], self.yuvref.video['Y'][i]))
        self.graph(x, y)
        return self.measure