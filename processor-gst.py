#!/usr/bin/env python
'''
Copyright (c) 2011 Joar Wandborg <http://wandborg.se>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

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
from function import transform,log_type,resample
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
        self.pickle = cPickle.Unpickler(open(args.in_file))
        if kwargs.get('src'):
            self.source_file = kwargs.get('src')
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
            data = self.pickle.load()
        except Exception:
            sys.stderr.write("could not pickle")
            return
        parameters = {"brightness":-00,"contrast":8}
        #data = np.linspace(0,240,320*240).reshape((320,240))
    #    data = resample(data.T,config)
        data = transform(data)
        #data = 10*np.log(data)
        data = self.renormalize(data, parameters)
        data = np.ascontiguousarray(np.uint8(data))
        src.emit('push-buffer', gst.Buffer(data.T.data))

    def setup_gstreamer(self):
        self.pipeline = gst.Pipeline('pipeline')
        source = gst.element_factory_make('appsrc', 'source')
        caps = gst.Caps('video/x-raw-gray, bpp=8, endianness=1234, width=320, height=240, framerate=(fraction)1/10')
        source.set_property('caps', caps)
        source.set_property('blocksize', 320*240*1)
        source.connect('need-data', self.needdata)
        colorspace = gst.element_factory_make('ffmpegcolorspace')
        caps = gst.Caps('video/x-raw-yuv, width=320, height=240, framerate=(fraction)1/10, format=(fourcc)Y8')
        if self.args.out_file is not None:
            sink = gst.element_factory_make("filesink")
            sink.set_property("location",self.args.out_file)
        else:
            sink = gst.element_factory_make('xvimagesink')
        sink.caps = caps
        self.pipeline.add(source, colorspace, sink)
        gst.element_link_many(source, colorspace, sink)
        return self.pipeline

def parse_arguments():
    flags = ['daemon']
    parser = argparse.ArgumentParser()
    parser.description = 'OCT client.'
    parser.add_argument('-i',dest='in_file', default=config['in_file'])
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
