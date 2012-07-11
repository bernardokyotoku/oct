#!/usr/bin/env python
import sys, subprocess, cPickle, numpy as np, Image, tempfile, os, logging
import processor
from configobj import ConfigObj
from PyQt4 import QtCore, QtGui, uic
#from PyQt4.QtGui import QAction, QMainWindow, QWidget, QApplication, qApp, QIcon, QTextEdit, QMenu, QGridLayout, QPushButton, QGraphicsView, QGraphicsScene, qBlue, QPen, QRadioButton, QGroupBox, QButtonGroup, QPixmap, QSizePolicy, QPainter, QFont, QFrame, QPallete
from PyQt4.QtGui import *
from PyQt4.QtCore import QLine, QString, QObject, SIGNAL, QLineF, QRectF, QRect, QPoint, QPointF
form_class, base_class = uic.loadUiType("front_window2.ui")
from numpy import *
from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
#from pyqtgraph.graphicsItems import ImageItem
import matplotlib, matplotlib.pyplot as plt, matplotlib.gridspec as gridspec
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
try:
    import ueye
except ImportError:
    sys.stderr.write("Cannot import ueye modules")
from CameraGraphicsView import CameraGraphicsView
import acquirer

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("test")

def gray2qimage(gray):
    """Convert the 2D numpy array `gray` into a 8-bit QImage with a gray
    colormap.  The first dimension represents the vertical image axis.
    http://www.mail-archive.com/pyqt@riverbankcomputing.com/msg17961.html"""
    if len(gray.shape) != 2:
        raise ValueError("gray2QImage can only convert 2D arrays")
    gray = np.require(gray, np.uint8, 'C')

    h, w = gray.shape

    result = QtGui.QImage(gray.data, w, h, QtGui.QImage.Format_Indexed8)
    result.ndarray = gray
    for i in range(256):
        result.setColor(i, QtGui.QColor(i, i, i).rgb())
    return result

class AcquirerProcessor(QtCore.QThread):
    def __init__(self, parent=None):
        self.config = parent.config
        QtCore.QThread.__init__(self, parent)

    def run(self):
        filename = self.config['raw_file']
        self.fd = open(filename)
        logger.debug("Creating unpickler")
        self.unpickler = cPickle.Unpickler(self.fd)
        while True:
            try:
                logger.debug("data_collector is waiting for data.")
                self.data = self.unpickler.load()
            except EOFError, e:
                logger.debug("End of file.")
                self.fd.close()
                return
            self.prev = self.data
            logger.debug("std dev %.2e"%np.std(self.data))
            parameters = {"brightness":-00, "contrast":2}
            self.data = processor.process(self.data, parameters, self.config)
            logger.debug("Emitting data ready to showing")
            logger.debug("std dev processed %.2e"%np.std(self.data))
            self.emit(QtCore.SIGNAL("data_ready(PyQt_PyObject)"), self.data)

class AcquirerProcessor2(QtCore.QThread):
    def __init__(self, parent = None):
        self.config = parent.config
        QtCore.QThread.__init__(self, parent)
        self.connect(parent, 
                     QtCore.SIGNAL("stop_acquistion()"), 
                     self.stop_acquisition)

    def run(self):
        acquirer.continue_scan = True
        self.data = []
        acquirer.scan(self.config, self.data, "continuous", self.data_ready)

    def data_ready(self, data):   
        self.data = data
        logger.debug("std dev %.2e"%np.std(self.data))
        parameters = {"brightness":-00, "contrast":2}
        self.data = processor.process(self.data, parameters, self.config)
        logger.debug("Emitting data ready to showing")
        logger.debug("std dev processed %.2e"%np.std(self.data))
        self.emit(QtCore.SIGNAL("data_ready(PyQt_PyObject)"), self.data)

    def stop_acquisition(self):
        acquirer.continue_scan = False

class OCT (QtGui.QMainWindow, form_class):
    def __init__(self,parent = None, selected = [], flag = 0, *args):
        QtGui.QWidget.__init__(self, parent, *args)
        self.setupUi(self)
        self.config = processor.parse_config()
        self.setup_plot()
#        self.setup_tomography()
#        self.setup_a_scan()
        self.setup_camera()
        self.setup_select_image()
        self.processed_data = []
        self.current_image = 0
        self.setup_show_scale()
        self.setup_data_collector()
        self.setup_signals()

    def setup_signals(self):
        signals = [
        ('start',               "clicked()",            'start_acquisition'),
        ('imagej',              "clicked()",            'image_j'),
        ('saturation_spinbox',  "valueChanged(double)", 'update_saturation'),
        ('start_camera_button', "clicked()",            'camera_button'),
        ('black_spinbox',       "valueChanged(double)", 'update_saturation'),
        ('stop_button',         "clicked()",            'setup_plot'),
        ]
        def connect(blob): 
            QObject.connect(
                    getattr(self, blob[0]), 
                    SIGNAL(blob[1]), 
                    getattr(self, blob[2])
                    )
        map(connect, signals)

    def camera_button(self):
        if self.start_camera_button.text() == "Start Camera":
            logger.info("Starting camera.")
            self.start_camera()
            self.start_camera_button.setText("Stop Camera")
        else:
            logger.info("Stop camera.")
            self.stop_camera()
            self.start_camera_button.setText("Start Camera")

    def stop_acquisition(self):
        self.emit(QtCore.SIGNAL("stop_acquistion()"))
        QObject.disconnect(self.start,SIGNAL("clicked()"),self.stop_acquisition),
        QObject.connect(self.start,SIGNAL("clicked()"),self.start_acquisition),
        self.start.setText("Start Acquisition")

    def start_camera(self):
        self.camera_device = ueye.camera(1)
        self.camera_device.AllocImageMem()
        self.camera_device.SetImageMem()
        self.camera_device.SetImageSize()
        self.camera_device.SetColorMode()
        self.camera_device.CaptureVideo()
        self.camera_timer = QtCore.QTimer()
        self.connect(self.camera_timer, 
                     QtCore.SIGNAL("timeout()"), 
                     self.update_camera_image_timer)
        self.update_camera_image()
        self.camera_timer.start(100)

    def update_saturation(self, new_value):
        self.zlim = [self.black_spinbox.value(), self.saturation_spinbox.value()]
        self.plot_in_tomography_view(self.processed_data[self.current_image])
       
    def hello(self):
        logger.debug("HELO")

    def setup_data_collector(self):
        self.DataCollector = AcquirerProcessor2(self)
        self.connect(self.DataCollector, SIGNAL("data_ready(PyQt_PyObject)"), self.add_data_and_update)

    def setup_show_scale(self):
        QObject.connect(self.show_scale_checkbox, SIGNAL("stateChanged( int )"), self.show_scale_event)

    def show_scale_event(self):
        if self.show_scale_checkbox.isChecked():
            self.make_scale()
        else :
            self.remove_scale()

    def closeEvent(self, event):
        pass
   
    def stop_camera(self):
        self.camera_timer.stop()
        self.camera_device.StopLiveVideo()
        self.camera_device.FreeImageMem()
        self.camera_device.ExitCamera()

    def image_j(self):
        filename = self.save_tiff(self.processed_data[self.current_image])
        subprocess.Popen(["imagej", '-o', filename], stdout = subprocess.PIPE)

    def save_tiff(self, data):
        data = data.T
        image = Image.frombuffer("L" ,data.shape ,data.data, 'raw', 'L', 0 ,1)
        fd, filename = tempfile.mkstemp(suffix = ".tiff")
        with os.fdopen(fd, 'w') as fp:
            image.save(fp = fp, format = "tiff")
        return filename

    def setup_select_image(self):
        QObject.connect(self.select_image, SIGNAL("valueChanged( int )"), self.update_image)
    def setup_plot(self):
        logger.debug("Setting plot up")
        self.dpi = 80
#        width = float(self.tomography_holder_widget.width())/self.dpi
#        height = float(self.tomography_holder_widget.height())/self.dpi
        self.width = 5.4
        height = 5.3
        self.fig = plt.figure(figsize = (self.width, height), dpi=self.dpi)
        self.gridspec = gridspec.GridSpec(1, 2, left = 0.05, width_ratios=[3,1])
        self.canvas = FigureCanvas(self.fig)
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        self.tomography_holder_widget.setLayout(vbox)
        self.canvas.setParent(self.tomography_holder_widget)
        self.canvas.mpl_connect('button_release_event', self.plot_button_released)
        self.setup_tomography()
        self.setup_a_scan()
        self.canvas.draw()

    def plot_button_released(self, event):
        if event.inaxes is self.tomography_ax:
            logger.debug("tomography axis clicked")
        elif event.inaxes is self.a_scan_ax:
            logger.debug("a_scan axis clicked")
        else:
            logger.debug("Button released X:%f, Y%f, axis %s"%(event.xdata, event.ydata, str(event.inaxes)))

    def setup_tomography(self):
        self.zlim = [None, None]
        self.tomography_ax = plt.subplot(self.gridspec[0])
        self.tomography_ax.plot()
       #self.fig.add_subplot(121)

#        self.tomography_scene = QGraphicsScene(0,0,640,480)
#        self.tomography_view.setScene(self.tomography_scene) 

#        self.tomography_scene.mousePressEvent = self.tomography_pressed
#        self.tomography_scene.mouseMoveEvent = self.tomography_pressed
#        self.make_scale()
#        self.plot_in_tomography_view(np.zeros((480,640)))
#        self.tomography_view.fitInView(QRectF(0,0,640,480), QtCore.Qt.KeepAspectRatio)
#        self.tomography_scene.mouseReleaseEvent = self.camera_released
    

    def make_scale(self):
        scene_rect = self.tomography_scene.sceneRect()
        bl = scene_rect.bottomRight()
        size = QtCore.QSizeF(scene_rect.width()/4,scene_rect.height()/20)
        self.scale_rect = QRectF(bl - QtCore.QPointF(size.width()+size.height(),size.height()*2), size)
        self.scale_item = self.tomography_scene.addRect(self.scale_rect, QPen(Qt.Qt.yellow, 1), QBrush(Qt.Qt.yellow, Qt.Qt.SolidPattern))

    def remove_scale(self):
        self.tomography_scene.removeItem(self.scale_item)

    def tomography_pressed(self, event):
        x = int(event.scenePos().x())
        if hasattr(self, "tomography_line_item"):
            self.tomography_scene.removeItem(self.tomography_line_item)
        yf = int(self.tomography_scene.sceneRect().top())
        y0 = int(self.tomography_scene.sceneRect().bottom())
        self.tomography_line_item = self.tomography_scene.addLine(x, y0, x, yf, QPen(Qt.Qt.yellow, 1, Qt.Qt.DotLine))
        if x >= self.current_tomography_data.shape[1]:
            x = self.current_tomography_data.shape[1] - 1
        elif x < 0:
            x = 0
        Y = self.current_tomography_data[:,x]
        X = np.linspace(10,0,len(Y))
        self.curve.setData(Y,X)
        self.plot.replot()

    def setup_a_scan(self):
        self.a_scan_ax = plt.subplot(self.gridspec[1])#self.fig.add_subplot(122)
        self.a_scan_ax.plot()
#        self.plot = Qwt.QwtPlot()
#        size_policy = QSizePolicy()
#        size_policy.setHorizontalStretch(1) 
#        size_policy.setHorizontalPolicy(size_policy.Preferred) 
#        size_policy.setVerticalPolicy(size_policy.Preferred) 
#        self.plot.setSizePolicy(size_policy)
##        self.plot.enableAxis(Qwt.QwtPlot.yLeft, False)
#        self.plot.enableAxis(Qwt.QwtPlot.xBottom, False)
#
#        grid = Qwt.QwtPlotGrid()
#        grid.attach(self.plot)
#        grid.setPen(Qt.QPen(Qt.Qt.white, 0, Qt.Qt.DotLine))
#        self.plot.setCanvasBackground(Qt.Qt.black)
#        self.plot_holder_widget.children()[0].addWidget(self.plot)
#
#        self.curve = Qwt.QwtPlotCurve()
#        self.curve.attach(self.plot)
#        self.curve.setPen(Qt.QPen(Qt.Qt.green, 1))

    def update_image(self, index):
        self.current_image = index - 1
        self.plot_in_tomography_view(self.processed_data[self.current_image])
        
    def setup_camera(self):
        self.camera_view = CameraGraphicsView()
        self.widget_7.children()[0].addWidget(self.camera_view)

        self.camera_scene = QGraphicsScene()
        self.camera_view.setScene(self.camera_scene)
        self.camera_scene.mousePressEvent = self.camera_pressed
        self.camera_scene.mouseMoveEvent = self.camera_moved
        self.camera_scene.mouseReleaseEvent = self.camera_released
        self.scan_type = 'continuous'
        QObject.connect(self.d2, SIGNAL('clicked()'), self.change_selector) 
        QObject.connect(self.d3, SIGNAL('clicked()'), self.change_selector) 
        self.d2.click()


    def update_camera_image(self):
        if hasattr(self,"camera_pixmap"):
            self.camera_scene.removeItem(self.camera_pixmap)
        self.camera_device.CopyImageMem()
        self.camera_image = gray2qimage(self.camera_device.data)
        pixmap_image = QtGui.QPixmap.fromImage(self.camera_image)
        self.camera_pixmap = self.camera_scene.addPixmap(pixmap_image)
        if hasattr(self, 'item'):
            self.camera_pixmap.stackBefore(self.item)
        self.camera_scene.setSceneRect(self.camera_pixmap.boundingRect())
        self.camera_view.fitInView(self.camera_pixmap, QtCore.Qt.KeepAspectRatio)

    def update_camera_image_timer(self):
        self.update_camera_image()
        self.camera_timer.start(500)

    def change_selector(self):
        if self.d2.isChecked():
            self.scan_type = "continuous"
            self.selector = lambda start, end: self.camera_scene.addLine(QLineF(start, end))
        else:
            self.scan_type = "3D"
            self.selector = self.select_rect
#            self.selector = lambda start, end: self.camera_scene.addRect(QRectF(start, end))

    def area_select(self, start, end):
        return self.camera_scene.addRect(QRectF(start, end))

    def camera_pressed(self, event):
        self.pressed_pos = event.scenePos()
        self.camera_moved(event)

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

    def camera_moved(self, event):
        if hasattr(self, "item"):
            self.camera_scene.removeItem(self.item)
#        start, end = self.fix_rect_points(self.pressed_pos, event.scenePos())
        start, end = self.pressed_pos, event.scenePos()
        self.item = self.selector(start, end)

    def camera_released(self, event):
        if hasattr(self, "item"):
            self.camera_scene.removeItem(self.item)
        self.released_pos = event.scenePos()
#        start, end = self.fix_rect_points(self.pressed_pos, event.scenePos())
        start, end = self.pressed_pos, event.scenePos()
        self.update_config_path(start, end)
        self.item = self.selector(start, end)

    def select_rect(self, start, end):
        start, end = self.fix_rect_points(start, end)
        return self.camera_scene.addRect(QRectF(start, end))

    def save_processed_data(self, filename):
        import h5py
        file = h5py.File(filename, 'w')
        root = file.create_group("root")
        for i, image in enumerate(self.processed_data):
            root.create_dataset('image_%03d'%i, image.shape, image.dtype) 
        file.close()

    def plot_in_tomography_view(self, data):
        logger.debug("ploting data %s, mean %.2e, min $.2e, max %.2e"%(str(data.shape),np.min(data),np.max(data)))
        self.current_tomography_data = data
        logger.debug("zlim in plot_in_tomography_view %s"%str(self.zlim))
        self.tomography_ax.clear()        
        self.tomography_ax.imshow(self.current_tomography_data,vmin=self.zlim[0],vmax=self.zlim[1])
        self.canvas.draw()

#        if hasattr(self, "tomography_item"):
#            self.tomography_scene.removeItem(self.tomography_item)
#        self.tomography_image = gray2qimage(data)
#        self.resize_tomography_view()
#        self.tomography_scene.setBackgroundBrush(QtGui.QBrush(self.tomography_image))
#        self.resize_tomography_view()
#        self.tomography_view.fitInView(self.tomography_scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def resize_tomography_view(self):
        holder_aspect_ratio = aspect_ratio(self.tomography_holder_widget.rect())
        tomography_aspect_ratio = aspect_ratio(self.tomography_image)
        if holder_aspect_ratio > tomography_aspect_ratio:
            width = self.tomography_holder_widget.width()
            self.tomography_view.setFixedHeight(tomography_aspect_ratio*width)
            self.tomography_view.setFixedWidth(width)
        else:
            height = self.tomography_holder_widget.height()
            self.tomography_view.setFixedWidth(height/tomography_aspect_ratio)
            self.tomography_view.setFixedHeight(height)

    def add_data_and_update(self, data):
        logger.debug("std dev %.2e, min %.2e, max %.2e"%(np.std(data), np.min(data), np.max(data)))
        self.processed_data += [data]
        n_images = len(self.processed_data)
        self.current_image = n_images - 1
        self.select_image.setMaximum(n_images)
        self.plot_in_tomography_view(data)
        self.saturation_spinbox.setValue(np.max(data))
        self.black_spinbox.setValue(np.min(data))

    def start_acquisition(self):
        self.DataCollector.start()
        QObject.disconnect(self.start,SIGNAL("clicked()"),self.start_acquisition),
        QObject.connect(self.start,SIGNAL("clicked()"),self.stop_acquisition),
        self.start.setText("Stop Acquisition")
#        cmd = ["python", "doct.py", "-o", self.config['raw_file'], "--scan-single" ]
#        self.acquisition = subprocess.Popen(cmd)

    def save_serie(self):
        if save_serie_dialog._exec():
            print save_serie_dialog.save_file_path.text()

save_series_form_class, save_series_base_class = uic.loadUiType("save_series.ui")
class SaveSerieDialog(QtGui.QDialog, save_series_form_class):
    def __init__(self,parent = None, selected = [], flag = 0, *args):
        QtGui.QWidget.__init__(self, parent, *args)
        self.setupUi(self)
        self.config = processor.parse_config()

    def fill_save_path(self):
        filename = QtGui.QFileDialog.getOpenFileName()
        self.save_file_path.setText(filename)

def aspect_ratio(item):
    return float(item.height())/float(item.width())
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main_window = OCT()
    save_serie_dialog = SaveSerieDialog()
    main_window.show()
    app.exec_()
