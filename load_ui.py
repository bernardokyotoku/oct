#!/usr/bin/env python
import sys
import math
import numpy as np
import gobject, pygst
pygst.require('0.10')
import gst
from subprocess import Popen
import processor as pro
import cPickle
from configobj import ConfigObj
from PyQt4 import QtCore, QtGui, uic
#from PyQt4.QtGui import QAction, QMainWindow, QWidget, QApplication, qApp, QIcon, QTextEdit, QMenu, QGridLayout, QPushButton, QGraphicsView, QGraphicsScene, qBlue, QPen, QRadioButton, QGroupBox, QButtonGroup, QPixmap, QSizePolicy, QPainter, QFont, QFrame, QPallete
from PyQt4.QtGui import *
from PyQt4.QtCore import QLine, QString, QObject, SIGNAL, QLineF, QRectF, QRect, QPoint, QPointF
form_class, base_class = uic.loadUiType("/home/bkyotoku/Projects/oct/front_window.ui")
from numpy import *
from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt

class Tomo(QWidget):
    def paintEvent(self, event):
        QWidget.paintEvent(self, event)
        painter = QPainter(self.tomography)
        painter.setClipRect(self.contentsRect())
        r = self.contentsRect()
        self.label.setText(str(r))
        painter.begin(self)
        painter.setPen(Qt.QPen(Qt.Qt.blue, 3, Qt.Qt.DotLine))
        painter.drawLine(QPoint(0, 0), QPoint(100, 100))
#        painter.setFont(QFont("Arial", 30))
#        painter.drawText(QRect(100,100), Qt.Qt.AlignCenter, "Qt")
        painter.end()
#        self.drawContents(painter)

class Overlay(QWidget):

    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, QtCore.Qt.transparent)
        self.setPalette(palette)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
#        painter.setRenderHint(QPainter.Antialiasing)
#        painter.fillRect(event.rect(), QBrush(QColor(255, 255, 255, 127)))
#        painter.setPen(QPen(QtCore.Qt.NoPen))
        painter.setPen(Qt.QPen(Qt.Qt.blue, 3, Qt.Qt.DotLine))
        painter.drawLine(QPoint(0, 0), QPoint(100, 100))
        for i in range(6):
            if (self.counter / 5) % 6 == i:
                painter.setBrush(QBrush(QColor(127 + (self.counter % 5)*32, 127, 127)))
            else:
                painter.setBrush(QBrush(QColor(127, 127, 127)))
                painter.drawEllipse(
                    self.width() /2 + 30 * math.cos(2 * math.pi * i / 6.0) - 10,
                    self.height()/2 + 30 * math.sin(2 * math.pi * i / 6.0) - 10,
                    20, 20)
        painter.end()

    def showEvent(self, event):
        self.timer = self.startTimer(50)
        self.counter = 0

    def timerEvent(self, event):
        self.counter += 1
        self.update()
        if self.counter == 60:
            self.killTimer(self.timer)
            self.hide()
 
class OCT (QtGui.QMainWindow, form_class):
    def __init__(self,parent = None, selected = [], flag = 0, *args):
        QtGui.QWidget.__init__(self, parent, *args)
        self.setupUi(self)
        QObject.connect(self.start, SIGNAL("clicked()"), self.start_acquisition)
        QObject.connect(self.imagej, SIGNAL("clicked()"), self.update_plot)
        self.windowId = self.tomography.winId()
        self.config = pro.parse_config()
        self.appsrc = True
#        self.tomography.paintEvent = self.paintEvente
#        self.setup_tomography()
    
        self.overlay = QGraphicsView(self.tomography)
#        self.overlay = Overlay(self.tomography)
        self.s = QGraphicsScene()
        self.overlay.setScene(self.s)
        self.setup_a_scan()
        self.setup_camera()

#    def paintEvent(self, event):
##    def dra(self):
##        QtGui.QMainWindow.paintEvent(self, event)
#        painter = QPainter()
##        painter.setClipRect(self.contentsRect())
##        r = self.contentsRect()
##        self.label.setText(str(r))
#        painter.begin(self)
#        painter.setPen(Qt.QPen(Qt.Qt.blue, 3, Qt.Qt.DotLine))
#        painter.drawLine(QPoint(0, 0), QPoint(100, 100))
##        painter.setFont(QFont("Arial", 30))
##        painter.drawText(QRect(100,100), Qt.Qt.AlignCenter, "Qt")
#        painter.end()
##        self.drawContents(painter)

    def setup_tomography(self):
        self.tomograhy = Tomo()
        self.windowId = self.tomography.winId()
        size_policy = QSizePolicy()
        size_policy.setHorizontalStretch(3) 
        size_policy.setHorizontalPolicy(size_policy.Preferred) 
        size_policy.setVerticalPolicy(size_policy.Preferred) 
        self.tomography.setSizePolicy(size_policy)
        self.widget_4.children()[0].addWidget(self.tomography)

    def setup_a_scan(self):
        self.plot = Qwt.QwtPlot()
        size_policy = QSizePolicy()
        size_policy.setHorizontalStretch(1) 
        size_policy.setHorizontalPolicy(size_policy.Preferred) 
        size_policy.setVerticalPolicy(size_policy.Preferred) 
        self.plot.setSizePolicy(size_policy)
#        self.plot.enableAxis(Qwt.QwtPlot.yLeft, False)
        self.plot.enableAxis(Qwt.QwtPlot.xBottom, False)

        grid = Qwt.QwtPlotGrid()
        grid.attach(self.plot)
        grid.setPen(Qt.QPen(Qt.Qt.white, 0, Qt.Qt.DotLine))
        self.plot.setCanvasBackground(Qt.Qt.black)
        self.widget_4.children()[0].addWidget(self.plot)

    
    def update_plot(self):
        self.overlay.show()
#        self.s.addLine(0, 0,100, 100,Qt.QPen(Qt.Qt.blue, 3, Qt.Qt.DotLine))
#        y = self.data.T[50]
#        x = np.linspace(0, 20,len(y))
#        self.label.setText(str(len(y)))
##        y = pi*sin(x)
#        curve = Qwt.QwtPlotCurve('y = pi*sin(x)')
#        curve.attach(self.plot)
#        curve.setPen(Qt.QPen(Qt.Qt.green, 1))
#        curve.setData(y, x)
#        self.plot.replot()

    def setup_camera(self):
        self.scene = QGraphicsScene()
        self.camera.setSceneRect(QRectF(self.tomography.geometry()))
        self.camera.setScene(self.scene)
        self.scene.mousePressEvent = self.camera_pressed
        self.scene.mouseMoveEvent = self.camera_moved
        self.scene.mouseReleaseEvent = self.camera_released
        self.scan_type = 'continuous'
        QObject.connect(self.d2, SIGNAL('clicked()'), self.change_selector) 
        QObject.connect(self.d3, SIGNAL('clicked()'), self.change_selector) 
        self.d2.click()

    def change_selector(self):
        if self.d2.isChecked():
            self.scan_type = "continuous"
            self.selector = lambda start, end: self.scene.addLine(QLineF(start, end))
        else:
            self.scan_type = "3D"
            self.selector = lambda start, end: self.scene.addRect(QRectF(start, end))

    def area_select(self, start, end):
        return self.scene.addRect(QRectF(start, end))

    def camera_pressed(self, event):
        self.pressed_pos = event.scenePos()

    def update_config_path(self, start, end):
        start = self.convert_to_path(start)
        end = self.convert_to_path(end)
        self.config[self.scan_type]['x0'] = start.x() 
        self.config[self.scan_type]['y0'] = start.y() 
        self.config[self.scan_type]['xf'] = start.x() 
        self.config[self.scan_type]['yf'] = start.y() 

    def convert_to_path(self, point):
        scale = self.config['camera_to_path_scale']
        return point*scale

    def fix_rect_points(self, A, B):
        x0 = min([A.x(), B.x()])
        xf = max([A.x(), B.x()])
        y0 = min([A.y(), B.y()])
        yf = max([A.y(), B.y()])
        return QPointF(x0, y0), QPointF(xf, yf)

    def camera_released(self, event):
        if hasattr(self, "item"):
            self.scene.removeItem(self.item)
        self.released_pos = event.scenePos()
        start, end = self.fix_rect_points(self.pressed_pos, event.scenePos())
        self.update_config_path(start, end)
        self.item = self.selector(start, end)

    def camera_moved(self, event):
        if hasattr(self, "item"):
            self.scene.removeItem(self.item)
        start, end = self.fix_rect_points(self.pressed_pos, event.scenePos())
        self.item = self.selector(start, end)

    def setup_gst(self):
        self.fd = open("raw_data")
        if self.appsrc:
            source = gst.element_factory_make('appsrc', 'source')
            frame_rate = 25 
            height = 240
            width = 320
            caps = gst.Caps("""video/x-raw-gray, 
                             bpp=8, 
                             endianness=1234, 
                             width=%d, 
                             height=%d, 
                             framerate=(fraction)%d/1"""%(width,height,frame_rate))
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
            self.data = self.unipickler.load()
        except Exception, e:
            print "end data"
            self.pipeline.set_state(gst.STATE_NULL)
            self.data = self.prev
        self.prev = self.data
        parameters = {"brightness":-00,"contrast":2}
        self.data = pro.process(self.data, parameters, self.config)
        src.emit('push-buffer', gst.Buffer(self.data.T.data))

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
