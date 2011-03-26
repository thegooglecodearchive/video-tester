# coding=UTF8

from VideoTester.config import vtLog

class Meter:
    def __init__(self):
        self.measures = []
    
    def run(self):
        measures = []
        for measure in self.measures:
            vtLog.info("- Measuring: " + measure.measure['name'])
            measures.append(measure.calculate())
        return measures

class Measure:
    def __init__(self):
        self.measure = dict()
        self.measure['name'] = None
        self.measure['units'] = None
        self.measure['type'] = None
    
    def calculate(self):
        pass
    
    def __max(self, x, y):
        i = y.index(max(y))
        return [x[i], y[i]]
    
    def __min(self, x, y):
        i = y.index(min(y))
        return [x[i], y[i]]
    
    def __mean(self, y):
        sum = 0
        for x in y:
            sum = sum + x
        return sum / len(y)
    
    def graph(self, x, y):
        self.measure['axes'] = [x, y]
        self.measure['max'] = self.__max(x, y)
        self.measure['min'] = self.__min(x, y)
        self.measure['mean'] = self.__mean(y)