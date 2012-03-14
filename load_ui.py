import sys
import gobject, pygst
pygst.require('0.10')
import gst
from subprocess import Popen
import processor as pro
import cPickle
from configobj import ConfigObj
from PyQt4 import QtCore,QtGui,uic
from PyQt4.QtGui import QAction, QMainWindow, QWidget, QApplication, qApp, QIcon, QTextEdit, QMenu, QGridLayout, QPushButton, QGraphicsView, QGraphicsScene, qBlue, QPen, QRadioButton, QGroupBox, QButtonGroup, QPixmap
from PyQt4.QtCore import QLine, QString, QObject, SIGNAL
form_class, base_class = uic.loadUiType("front_window.ui")
 
class OCT (QtGui.QMainWindow, form_class):
    def __init__(self,parent=None,selected=[],flag=0,*args):
        QtGui.QWidget.__init__(self,parent,*args)
        self.setupUi(self)
        self.windowId = self.findChild(QWidget,"tomography").winId()
        start_button = self.findChild(QPushButton,'start')
        QObject.connect(start_button,SIGNAL("clicked()"),self.start_acquisition)
        self.config = pro.parse_config()
        self.appsrc = True

    def setup_gst(self):
        self.fd = open("raw_data")
        if self.appsrc:
            source = gst.element_factory_make('appsrc', 'source')
            frame_rate = 25 
            height = 240
            width = 320
            caps = gst.Caps('video/x-raw-gray, bpp=8, endianness=1234, width=%d, height=%d, framerate=(fraction)%d/1'%(width,height,frame_rate))
            source.set_property('caps', caps)
            source.set_property('blocksize', width*height*1)
            source.connect('need-data', self.needdata)
            colorspace = gst.element_factory_make("ffmpegcolorspace")
        else:
            source = gst.element_factory_make("v4l2src", "vsource")
            source.set_property("device", "/dev/video0")
        sink = gst.element_factory_make("xvimagesink", "sink")

        self.pipeline = gst.Pipeline("pipeline")
        self.pipeline.add(source, colorspace, sink)
        gst.element_link_many(source, colorspace, sink)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)

    def needdata(self, src, length):
        try:
            data = self.unipickler.load()
        except Exception, e:
#            self.fd.close()
#            self.fd = open("raw_data")
#            self.unipickler = cPickle.Unpickler(self.fd)
            print "end data"
            self.pipeline.set_state(gst.STATE_NULL)
            data = self.prev
        self.prev = data
        parameters = {"brightness":-00,"contrast":2}
        data = pro.process(data,parameters,self.config)
        src.emit('push-buffer', gst.Buffer(data.T.data))

    def demuxer_callback(self, demuxer, pad):
        if pad.get_property("template").name_template == "video_%02d":
            queuev_pad = self.queuev.get_pad("sink")
            pad.link(queuev_pad)

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.pipeline.set_state(gst.STATE_NULL)
            print "end of message"
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.pipeline.set_state(gst.STATE_NULL)

    def on_sync_message(self, bus, message):
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            win_id = self.windowId
            assert win_id
            imagesink = message.src
            imagesink.set_xwindow_id(win_id)

    def start_prev(self):
        self.setup_gst()
        self.unipickler = cPickle.Unpickler(self.fd)
        self.pipeline.set_state(gst.STATE_PLAYING)
        print "should be playing"

    def start_acquisition(self):
        from subprocess import Popen 
        self.acquisition = Popen(["python","image_generator.py",
                                  "-a","--count=10","--rate=25"],)
        self.start_prev()
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main_window = OCT()
    main_window.show()
    app.exec_()
