'''
Copyright (c) 2011 Joar Wandborg <http://wandborg.se>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

- A response to http://stackoverflow.com/questions/8187257/play-audio-and-video-with-a-pipeline-in-gstreamer-python/8197837
- Like it? Buy me a beer! https://flattr.com/thing/422997/Joar-Wandborg
'''
import gst
import gobject
gobject.threads_init()
import logging
import numpy as np


logging.basicConfig()

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)


class VideoPlayer(object):
	'''
	Simple video player
	'''
	def needdata(self, src, length):
		bytes = np.int16(np.random.rand(length/2)*30000).data
		src.emit('push-buffer', gst.Buffer(bytes))

	def __init__(self, **kwargs):
		self.loop = gobject.MainLoop()

		if kwargs.get('src'):
			self.source_file = kwargs.get('src')

		self.__setup_pipeline()

	def run(self):
		self.pipeline.set_state(gst.STATE_PLAYING)
		self.loop.run()

	def stop(self):
		self.loop.quit()


	def __setup_pipeline(self):
		self.pipeline = gst.Pipeline("pipeline")
		source = gst.element_factory_make("appsrc", "source")
		caps = gst.Caps("video/x-raw-gray,bpp=16,endianness=1234,width=320,height=240,framerate=(fraction)10/1")
		source.set_property('caps',caps)
		source.set_property('blocksize',320*240*2)
		source.connect('need-data', self.needdata)
		colorspace = gst.element_factory_make('ffmpegcolorspace')
		enc = gst.element_factory_make('theoraenc')
		mux = gst.element_factory_make('oggmux')
		caps = gst.Caps("video/x-raw-yuv,width=320,height=240,framerate=(fraction)10/1,format=(fourcc)I420")
		enc.caps = caps
		videosink = gst.element_factory_make('xvimagesink')
		videosink.caps = caps

		self.pipeline.add(source, colorspace, videosink)
		gst.element_link_many(source, colorspace, videosink)
		return self.pipeline
		

if __name__ == '__main__':
	player = VideoPlayer()
	player.run()
