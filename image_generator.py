#!/usr/bin/env python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
import numpy as np
import matplotlib.pyplot as plt
import cPickle
from time import sleep
import Image

def parse():
    import argparse
    parser = argparse.ArgumentParser()
    parser.description = "Raw data simulator."
    parser.add_argument('-o',dest='out_file', default='raw_data')
    parser.add_argument('--count',dest='count', default=1, help='Number of frames to generate.')
    parser.add_argument('--height',dest='height', default=240)
    parser.add_argument('--width',dest='width', default=320)
    parser.add_argument('--rate',dest='rate', default=1, help='Rate frames are generated.')
    parser.add_argument('-',dest='stdout', action='store_true')
    parser.add_argument('-p', action='store_true', help='Plot image') 
    parser.add_argument('-a', action='store_true', help='send to file')
    parser.add_argument('-d', action='store_true') 
    parser.add_argument('-n', action='store_true') 
    parser.add_argument('-f', action='store_true', help='Spaced equally in frequency')
    return parser.parse_args()
arg = parse()

width = arg.width
height = arg.height
f = arg.f

def matrix(phase):
    def gauss(x,x0,d):
        return np.exp(-((x-x0)/d)**2)

    def spectrum(L):
        spectral_range = np.array([1.25,1.35]) #wavelength
        lmbd0 = 1.3
        Dlmbd = 0.02
        
        c = 3E8 # micrometers/microseconds
        if f:
            spectral_range = c/spectral_range 
        x = np.linspace(spectral_range[0],spectral_range[1],width)
        if f:
            spectral_range = c/spectral_range 
            x = c/x
        lmbd = x
        spect = np.cos(2*np.pi*L/lmbd)*gauss(lmbd,lmbd0,Dlmbd)
        return spect
    lengths = 500*np.sin(phase + 4*np.linspace(0,2,height)) + 1000
    return np.vstack([spectrum(L) for L in lengths])

continue_scan = True

i = 0
def fill_with_simulation(memory):
    global i, width, height
    width, height = memory.shape
    moving_factor = 0.1
    m = matrix(i*moving_factor)
    i += 1
    logger.debug("Filling with data whose std is %e.2"%np.std(m))
    np.copyto(memory, m.T)


def scan(config,data,mode,data_ready):
    global continue_scan
    continue_scan = True
    i = 0
    while continue_scan:
        moving_factor = 0.1
        m = matrix(i*moving_factor)
        i += 1
        data_ready(m)
        if mode == "single":
            continue_scan = False
        sleep(1.0/float(arg.rate))

class Scope:
    def __init__(self, device):
        self.i = 0
        logger.debug("Scope initatied device %s"%device)

    def ConfigureHorizontalTiming(self, **config):
        logger.debug("configuring horizontal timming")

    def ExportSignal(self, **config):
        logger.debug("configuring export signal")

    def ConfigureTrigger(self, **config):
        logger.debug("configuring trigger")

    def ConfigureVertical(self, **config):
        logger.debug("configuring vertical")

    def InitiateAcquisition(self):
        logger.debug("initiating acquisition")

    def Fetch(self, ch, memory):
        logger.debug("Fetching data to memory position %d"%id(memory))
        global width, height, f
        f = True
        width, height = memory.shape
        moving_factor = 0.1
        m = matrix(self.i*moving_factor)
        self.i += 1
        logger.debug("Filling with data whose std is %e.2"%np.std(m))
        memory[:] = 10000*m.T

def main():
    if arg.a:
        fd = open(arg.out_file,'w',0)
        pickler = cPickle.Pickler(fd,cPickle.HIGHEST_PROTOCOL)
    for i in range(int(arg.count)):
        moving_factor = 0.1
        print "Creating image", i, "."
        m = matrix(i*moving_factor)
        if arg.p:
            plt.figure()
            plt.imshow(m)
            plt.show()
            break

        if arg.a:
            try:
                pickler.dump(m)
            except Exception, e:
                print "Error", e.message
                break
        sleep(1.0/float(arg.rate))
    if arg.a:
        fd.close()

if __name__ == "__main__":
#    exit = False
#    while not exit or arg.n:
        main()
