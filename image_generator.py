#!/usr/bin/env python
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
    parser.add_argument('--count',dest='count', default=1)
    parser.add_argument('--height',dest='height', default=240)
    parser.add_argument('--width',dest='width', default=320)
    parser.add_argument('--rate',dest='rate', default=1)
    parser.add_argument('-',dest='stdout', action='store_true')
    parser.add_argument('-p', action='store_true') # plot image
    parser.add_argument('-a', action='store_true') # not pipe
    parser.add_argument('-d', action='store_true') 
    parser.add_argument('-n', action='store_true') 
    parser.add_argument('-R', action='store_true') #reciprocal
    parser.add_argument('-f', action='store_true') #reciprocal
    return parser.parse_args()
arg = parse()

def matrix(phase):
    def gauss(x,x0,d):
        return np.exp(-((x-x0)/d)**2)

    def spectrum(L):
        spectral_range = np.array([1.250,1.350]) #wavelength
        lmbd0 = 1.300
        Dlmbd = 0.02
        
        c = 3E8 # micrometers/microseconds
        if arg.f:
            spectral_range = c/spectral_range 
        x = np.linspace(spectral_range[0],spectral_range[1],arg.width)
        if arg.f:
            spectral_range = c/spectral_range 
            x = c/x
        lmbd = x
        spect = np.cos(2*np.pi*L/lmbd)*gauss(lmbd,lmbd0,Dlmbd)
        return spect

    def line(f):
        t = np.linspace(10000,11000,arg.width)
        if arg.R:
            t = 10000000/t
        carrier = np.sin(0.1*f*t)
        envelope = gauss(np.linspace(0,10,arg.width),5,1)
        return envelope*carrier
    frequencies = 2*np.sin(phase + 2*np.linspace(0,2,arg.height)) + 3
    lengths = 30*np.sin(phase + 4*np.linspace(0,2,arg.height)) + 60
    lengths = lengths*0.5
    return np.vstack([line(f) for f in frequencies])
#    return np.vstack([spectrum(L) for L in lengths])

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
        if (i >= int(arg.count)):
            print "exit"
            return True
    if arg.a:
        fd.close()

if __name__ == "__main__":
#    exit = False
#    while not exit or arg.n:
        main()
