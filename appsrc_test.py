#!/usr/bin/env python
import sys, os, pygtk, gtk, gobject
import pygst
pygst.require("0.10")
import gst
import numpy as np

def needdata( src, length):
	bytes = np.int16(np.random.rand(length/2)*30000).data
	src.emit('push-buffer', gst.Buffer(bytes))

player = gst.Pipeline("player")
source = gst.element_factory_make("appsrc", "source")
caps = gst.Caps("video/x-raw-gray,bpp=16,endianness=1234,width=320,height=240,framerate=(fraction)10/1")
source.set_property('caps',caps)
source.set_property('blocksize',320*240*2)
source.connect('need-data', needdata)
colorspace = gst.element_factory_make('ffmpegcolorspace')
enc = gst.element_factory_make('theoraenc')
mux = gst.element_factory_make('oggmux')
shout = gst.element_factory_make('shout2send')
shout.set_property("ip","localhost")
shout.set_property("password","hackme")
shout.set_property("mount","/stream")
caps = gst.Caps("video/x-raw-yuv,width=320,height=240,framerate=(fraction)10/1,format=(fourcc)I420")
enc.caps = caps
videosink = gst.element_factory_make('xvimagesink')
videosink.caps = caps

player.add(source, colorspace, videosink)
gst.element_link_many(source, colorspace, videosink)
player.set_state(gst.STATE_PLAYING)


gtk.gdk.threads_init()
