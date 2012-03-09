#!/usr/bin/python
import gobject, pygst
pygst.require('0.10')
import gst
from PyQt4 import QtGui 
from PyQt4.QtGui import QAction, QMainWindow, QWidget, QApplication, qApp, QIcon, QTextEdit, QMenu, QGridLayout, QPushButton, QGraphicsView, QGraphicsScene, qBlue, QPen, QRadioButton, QGroupBox, QButtonGroup, QPixmap
from PyQt4.QtCore import QLine, QString, QObject, SIGNAL
import sys
from subprocess import Popen
import processorg as pro
import cPickle
from configobj import ConfigObj

class CameraScene(QGraphicsScene):
    def __init__(self):
        super(CameraScene, self).__init__()
        self.start_point = None
        self.x1 = None
        self.y1 = None
        self.selection_type = '2D'
        self.setSceneRect(0,0,100,100)

    def mousePressEvent(self,event):
        self.start_point = event.scenePos()
        self.x1 = self.start_point.x()
        self.y1 = self.start_point.y()

    def mouseMoveEvent(self,event):
        map(self.removeItem,self.items())
        x2 = event.scenePos().x()
        y2 = event.scenePos().y()
        select = {'2D':self.addLine,'3D':self.addRectCoor}[self.selection_type]
        select(self.x1,self.y1,x2,y2)

    def addRectCoor(self,x1,y1,x2,y2):
        width = x2-x1    
        height = y2-y1
        x = (x2,-width) if width < 0 else (x1,width)
        y = (y2,-height) if height < 0 else (y1,height)
        self.addRect(x[0],y[0],x[1],y[1])

class OCT(QMainWindow):
    def __init__(self):
        super(OCT, self).__init__()
        self.out_file = "gst_pipe"
        self.initUI()
        self.config = pro.parse_config()

    def initUI(self):
        container = QWidget()
        self.setCentralWidget(container)
        self.exitAction = QAction('Exit',self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(qApp.quit)

        self.makeMenus()

        pane_right = self.makeRightPane()
        pane_left = self.makeLeftPane()

        grid = QGridLayout()
        grid.addWidget(pane_left,0,0)
        grid.addWidget(pane_right,0,1)
        grid.setColumnStretch(0,2)
        container.setLayout(grid)

        self.setGeometry(300,300,500,360)
        self.statusBar().showMessage("Ready")
        self.setWindowTitle("OCT")
        self.show()

    def setup_gst(self):
        self.fd = open("raw_data")
        if self.out_file is not None:
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

    def makeMenus(self):
        menuBar = self.menuBar()
        menuFile = menuBar.addMenu('File')
        menuEdit = menuBar.addMenu('Edit')
        menuFile.addAction(self.exitAction)

    def makeRightPane(self):
        buttonQuit = QPushButton('hello')
        button_start = QPushButton('Start')
        self.camera_view = QGraphicsView(CameraScene())
        pane_scan_type = self.makeScanTypeButtons()
        QObject.connect(button_start, SIGNAL("clicked()"), self.start_prev)

        pane_right = QWidget()
        grid_right = QGridLayout()
        grid_right.addWidget(buttonQuit,0,0)
        grid_right.addWidget(button_start,1,0)
        grid_right.addWidget(pane_scan_type,2,0)
        grid_right.addWidget(self.camera_view,3,0)
        pane_right.setLayout(grid_right)
        return pane_right

    def start_acquisition(self):
        from subprocess import Popen
        #self.acquisition = Popen(["acquirer.py","--continuous"])
        self.acquisition = Popen(["python","image_generator.py","-q"])

    def stop_acquisition(self):
        self.acquisition.terminate()

    def makeLeftPane(self):
        self.tomography_view = QWidget()
        self.plot_view = QGraphicsView(QGraphicsScene())

        pane_left = QWidget()
        grid_left = QGridLayout()
        grid_left.addWidget(self.plot_view,0,0)
        grid_left.addWidget(self.tomography_view,0,1)
        grid_left.setColumnStretch(1,2)
        pane_left.setLayout(grid_left)
        #winId fetched after placing in grid
        self.windowId = self.tomography_view.winId()
        return pane_left

    def makeScanTypeButtons(self):
        buttons_scan_type = [QRadioButton("2D"),QRadioButton("3D")]
        pane_scan_type = QGroupBox()
        group_scan_type = QButtonGroup()
        map(group_scan_type.addButton,buttons_scan_type)

        group_scan_type.buttonClicked.connect(self.f)
        layout_scan_type = QGridLayout()
        layout_scan_type.addWidget(buttons_scan_type[0],0,0)
        layout_scan_type.addWidget(buttons_scan_type[1],0,1)
        pane_scan_type.setLayout(layout_scan_type)
        buttons_scan_type[0].click()
        return pane_scan_type

    def f(self,event):
        t = str(event.sender().checkedButton().text())
        sys.stderr.write(t)
        self.camera_view.scene().selection_type = t

def getZoom(self):
    def zoom(event):
        self.scale(1.2,1.2) if event.delta()>0 else self.scale(0.8,0.8)
    return zoom

#    ex.tomography_view.scene().addPixmap(QPixmap("CNH.jpg"))
#    tomography = ex.tomography_view
#    tomography.wheelEvent = getZoom(tomography)

if __name__ == "__main__":
    #acquisition = Popen(["python","image_generator.py",])
    gobject.threads_init()
    #processor = Popen(["python", "processor-gst.py", "-o gst_pipe"])
    app = QtGui.QApplication(sys.argv)
    ex = OCT()
    #ex.setup_gst()
    #ex.start_prev()
    sys.exit(app.exec_())
