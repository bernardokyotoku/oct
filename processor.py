#!/usr/bin/env python
'''

- A response to http://stackoverflow.com/questions/8187257/play-audio-and-video-with-a-pipeline-in-gstreamer-python/8197837
- Like it? Buy me a beer! https://flattr.com/thing/422997/Joar-Wandborg

Pixel formats you a looking for this http://fourcc.org/
'''
import gobject
gobject.threads_init()
import logging
import numpy as np
import matplotlib.pyplot as plt
from configobj import ConfigObj
from validate import Validator
#from acquirer import log_type,resample
import argparse
import sys
import cPickle
from scipy import interpolate


logging.basicConfig()

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

def log_type(value):
    try:
        return getattr(logging,value)
    except AttributeError:
        pass
    return int(value)    

def renormalize(data,parameters):
    data = data + parameters['brightness']
    data = data * parameters['contrast']
    return data

def transform(rsp_data):
    return np.abs(np.fft.fft(rsp_data))

def resample(raw_data,config,rsp_data=None,axis=0):
    if rsp_data == None:
        n = config['numLongPts']
        rsp_data = np.zeros((n,raw_data.shape[-1]))
    else:
        n = rsp_data.shape[axis]
    p = [config['resample_poly_coef']['p%d'%i] for i in range(8)]
    f = np.poly1d(p)
    old_x = f(np.arange(raw_data.shape[axis]))
    new_x = np.linspace(0,raw_data.shape[axis],n)
    if len(raw_data.shape) == 1:
        tck = interpolate.splrep(old_x,raw_data,s=0)
        rsp_data = interpolate.splev(new_x,tck)
    else:
        for line in range(raw_data.shape[-1]):
            tck = interpolate.splrep(old_x,raw_data[:,line])
            rsp_data[:,line] = interpolate.splev(new_x,tck)
    return rsp_data

def process(data,parameters,config):
    data = resample(data, config)
    data = transform(data.T).T
    data = 10*np.log(data)
#    data = renormalize(data,parameters)
#    data = np.ascontiguousarray(np.uint8(data))
    return data

def process2(data,parameters,config):
    data = transform(data)
    data = 10*np.log(data)
#    data = renormalize(data,parameters)
#    data = np.ascontiguousarray(np.uint8(data))
    return data

def parse_arguments():
    flags = ['daemon']
    parser = argparse.ArgumentParser()
    parser.description = 'OCT client.'
    parser.add_argument('-i',dest='in_file', default = "raw_data" )
    parser.add_argument('-o',dest='out_file')
    for flag in flags:
        parser.add_argument('--' + flag,action='store_true',default=False) 
    return parser.parse_args()

def parse_config():
    validator = Validator({'log':log_type,'float':float})
    config = ConfigObj('config.ini', configspec='configspec.ini')
    if not config.validate(validator):
        raise Exception('config.ini does not validate with configspec.ini.')
    return config

if __name__ == '__main__':
    config = parse_config()
    args = parse_arguments()
    logging.basicConfig(filename='oct.log',level=config['log'])
    player = Processor(args)
    player.run()
