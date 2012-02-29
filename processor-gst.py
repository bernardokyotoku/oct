#!/usr/bin/env python
'''

- A response to http://stackoverflow.com/questions/8187257/play-audio-and-video-with-a-pipeline-in-gstreamer-python/8197837
- Like it? Buy me a beer! https://flattr.com/thing/422997/Joar-Wandborg

Pixel formats you a looking for this http://fourcc.org/
'''
import gst
import gobject
gobject.threads_init()
import logging
import numpy as np
import matplotlib.pyplot as plt
from configobj import ConfigObj
from validate import Validator
from acquirer import log_type,resample
import argparse
import sys
import cPickle


logging.basicConfig()

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)



class Processor(object):
    '''
    '''

    def __init__(self, args, **kwargs):
        self.loop = gobject.MainLoop()
        self.args = args
        self.unipickler = cPickle.Unpickler(open(args.in_file,buffering=100000000))
        self.setup_gstreamer()

    def run(self):
        self.pipeline.set_state(gst.STATE_PLAYING)
        self.loop.run()

    def stop(self):
        self.loop.quit()

    def renormalize(self,data,parameters):
        data = data + parameters['brightness']
        data = data * parameters['contrast']
        return data

    def needdata(self, src, length):
        try:
            data = self.unipickler.load()
        except Exception, e:
            sys.stderr.write(str(e))
            return
        parameters = {"brightness":-00,"contrast":8}
        data = process(data,parameters,config)
        src.emit('push-buffer', gst.Buffer(data.T.data))

    def setup_gstreamer(self):
        self.pipeline = gst.Pipeline('pipeline')
        vsource = gst.element_factory_make('appsrc', 'source')
        frame_rate = 7
        height = 240
        width = 320
        caps = gst.Caps('video/x-raw-gray, bpp=8, endianness=1234, width=%d, height=%d, framerate=(fraction)%d/1'%(width,height,frame_rate))
        vsource.set_property('caps', caps)
        vsource.set_property('blocksize', width*height*1)
        vsource.connect('need-data', self.needdata)
        filter = gst.element_factory_make('capsfilter')
        colorspace = gst.element_factory_make("ffmpegcolorspace")
        caps = gst.Caps('video/x-raw-yuv,format=(fourcc)I420,width=%d,height=%d,framerate=(fraction)%d/1'%(width,height,frame_rate))
        filter.set_property('caps', caps)
        queuev = gst.element_factory_make("queue", "queuev")
        if self.args.out_file is not None:
            asource = gst.element_factory_make("audiotestsrc", 'asource')
            conv = gst.element_factory_make("audioconvert") 
            conv.caps = gst.Caps('audio/x-raw-int,rate=44100,channels=2') 
            queuea = gst.element_factory_make("queue","queuea")
            avimux = gst.element_factory_make("avimux")
            sink = gst.element_factory_make("filesink")
            sink.set_property("location",self.args.out_file)

            self.pipeline.add(vsource,filter,colorspace,queuev,avimux,sink)
            gst.element_link_many(vsource, colorspace, filter, queuev, avimux, )
            gst.element_link_many(avimux, sink)
        else:
            pipeline_args += [sink]
            self.pipeline.add(*pipeline_args)
            gst.element_link_many(*pipeline_args)
        return self.pipeline

def renormalize(data,parameters):
    data = data + parameters['brightness']
    data = data * parameters['contrast']
    return data

def transform(rsp_data):
	return abs(np.fft.fft(rsp_data))

def process(data,parameters,config):
#	data = resample(data.T,config)
    data = transform(data)
    #data = 10*np.log(data)
    data = renormalize(data,parameters)
    data = np.ascontiguousarray(np.uint8(data))
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
