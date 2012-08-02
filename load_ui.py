#!/usr/bin/env python
import sys, subprocess, cPickle, numpy as np, Image, tempfile, os, logging, datetime, hardware_control as hc
from configobj import ConfigObj
from PyQt4 import QtCore, QtGui, uic
from Queue import Queue
#from PyQt4.QtGui import QAction, QMainWindow, QWidget, QApplication, qApp, QIcon, QTextEdit, QMenu, QGridLayout, QPushButton, QGraphicsView, QGraphicsScene, qBlue, QPen, QRadioButton, QGroupBox, QButtonGroup, QPixmap, QSizePolicy, QPainter, QFont, QFrame, QPallete
from PyQt4.QtGui import *
from PyQt4.QtCore import QLine, QString, QObject, SIGNAL, QLineF, QRectF, QRect, QPoint, QPointF
form_class, base_class = uic.loadUiType("front_window2.ui")
from save_serie import SaveOptionDialog
from numpy import *
from PyQt4 import Qt
#import PyQt4.Qwt5 as Qwt
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
try:
    import acquirer
except ImportError:
    import image_generator as acquirer
import processor

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


class AcquirerProcessor2(QtCore.QThread):
    def __init__(self, parent = None):
        self.parent = parent
        self.config = parent.config
        QtCore.QThread.__init__(self, parent)
        self.connect(parent, 
                     QtCore.SIGNAL("stop_acquistion()"), 
                     self.stop_acquisition)

    def run(self):
        scan_type = self.parent.scan_type
        acquirer.continue_scan = True
        self.data = []
        acquirer.scan(self.config, self.data, scan_type, self.push)
        self.emit(QtCore.SIGNAL("acq_finished_event()"))

    def push(self, data):
        logger.debug("pushing data to queue")
        self.parent.processor.queue.put(data)
        size = self.parent.processor.queue.qsize()
        self.emit(QtCore.SIGNAL("queue_size(int)"),size)

    def data_ready(self, data):   
        logger.debug("std dev %.2e"%np.std(data))
        parameters = {"brightness":-00, "contrast":2}
        data = processor.process(data, parameters, self.config)
        logger.debug("Emitting data ready to showing")
        logger.debug("std dev processed %.2e"%np.std(data))
        logger.debug("data dim %s"%str(data.shape))
        self.emit(QtCore.SIGNAL("data_ready(PyQt_PyObject)"), data)

    def stop_acquisition(self):
        acquirer.continue_scan = False

class Processor(QtCore.QThread):
    def __init__(self, parent = None):
        self.parent = parent
        self.config = parent.config
        QtCore.QThread.__init__(self, parent)
        self.terminated = False
        self.queue = Queue()

    def run(self):
        logger.debug("Processor running")
        while not self.terminated:
            logger.debug("Getting data from queue")
            data = self.queue.get(block=True)
            self.process(data)

    def process(self, data):
        logger.debug("std dev %.2e"%np.std(data))
        parameters = {"brightness":-00, "contrast":2}
        data = processor.process(data, parameters, self.config)
        logger.debug("Emitting data ready to showing")
        logger.debug("std dev processed %.2e"%np.std(data))
        logger.debug("data dim %s"%str(data.shape))
        self.emit(QtCore.SIGNAL("data_ready(PyQt_PyObject)"), data)

    def block_after_acquisition(self):
        self.queue.maxsize = 1

    def buffer_acquisition(self):
        self.queue.maxsize = 0

class OCT (QtGui.QMainWindow, form_class):
    def __init__(self,parent = None, selected = [], flag = 0, *args):
        QtGui.QWidget.__init__(self, parent, *args)
        self.setupUi(self)
        self.setup_icon()
        self.config = processor.parse_config()
        self.setup_tomography()
        self.setup_a_scan()
        self.setup_camera()
        self.processed_data = []
        self.current_image = 0
        self.setup_data_collector()
        self.setup_signals()
        self.apply_config()

    def setup_icon(self):
        icon = QIcon('icon.png')
        self.setWindowIcon(icon)

    def apply_config(self):
        self.update_n_lines_spinbox()
        self.update_n_images_spinbox()

    def laser_pointer(self, state):
        hc.turn_laser('on' if state else 'off')

    def setup_signals(self):
        signals = [
        ('start',               "clicked()",            'start_acquisition'),
        ('imagej',              "clicked()",            'image_j'),
        ('saturation_spinbox',  "valueChanged(double)", 'update_saturation'),
        ('lock_adjust_checkbox',"stateChanged(int)",       'lock_adjust'),
        ('start_camera_button', "clicked()",            'camera_button'),
        ('black_spinbox',       "valueChanged(double)", 'update_saturation'),
        ('exposure_spinbox',    "valueChanged(double)", 'set_exposure'),
        ('select_image',        "valueChanged(int)",   'update_image'),
        ('n_lines_spinbox',     "valueChanged(int)",   'update_n_lines'),
        ('n_images_spinbox',    "valueChanged(int)",   'update_n_images'),
        ]
        def connect(blob): 
            QObject.connect(
                    getattr(self, blob[0]), 
                    SIGNAL(blob[1]), 
                    getattr(self, blob[2])
                    )
        map(connect, signals)

    def lock_adjust(self, state):
        if state == Qt.Qt.Checked:
            logger.debug("checking lock adjust")
            self.black_spinbox.setEnabled(False)
            self.saturation_spinbox.setEnabled(False)
        elif state == Qt.Qt.Unchecked:
            logger.debug("unchecking lock adjust")
            self.black_spinbox.setEnabled(True)
            self.saturation_spinbox.setEnabled(True)
        

    def report_queue_size(self, size):
        self.statusBar().showMessage('Queue size %d'%size)

    def update_n_lines_spinbox(self):
        self.n_lines_spinbox.setValue(self.config[self.scan_type]['numRecords'])

    def update_n_images_spinbox(self):
        self.n_images_spinbox.setValue(self.config[self.scan_type]['numTomograms'])

    def update_n_lines(self, n):
        self.config[self.scan_type]['numRecords'] = n

    def update_n_images(self, n):
        self.config[self.scan_type]['numTomograms'] = n


    def camera_button(self):
        if self.start_camera_button.text() == "Start Camera":
            logger.info("Starting camera.")
            self.start_camera()
            self.start_camera_button.setText("Stop Camera")
        else:
            logger.info("Stop camera.")
            self.stop_camera()
            self.start_camera_button.setText("Start Camera")

    def set_exposure(self, time):
        self.camera_device.Exposure(time)

    def stop_acquisition(self):
        self.emit(QtCore.SIGNAL("stop_acquistion()"))

    def acquisition_finished(self):
        QObject.disconnect(self.start,SIGNAL("clicked()"),self.stop_acquisition),
        QObject.connect(self.start,SIGNAL("clicked()"),self.start_acquisition),
        self.start.setText("Start Acquisition")

    def open_save_option_dialog(self):
        save_option_dialog = SaveOptionDialog(self)
        save_option_dialog.show()
        

    def start_camera(self):
        self.camera_device = ueye.camera(1)
        self.camera_device.AllocImageMem()
        self.camera_device.SetImageMem()
        self.camera_device.SetImageSize()
        self.camera_device.SetColorMode()
        self.set_exposure(self.exposure_spinbox.value())
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
        self.processor = Processor(self)
        self.DataCollector = AcquirerProcessor2(self)
        self.connect(self.processor, SIGNAL("data_ready(PyQt_PyObject)"), self.add_data_and_update)
        self.connect(self.DataCollector, SIGNAL("acq_finished_event()"), self.acquisition_finished)
        self.connect(self.DataCollector, SIGNAL("queue_size(int)"), self.report_queue_size)
        self.processor.start()

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
        fd, filename = self.make_temp_filename()
        self.save_tiff(self.processed_data[self.current_image], filename)
        subprocess.Popen(["imagej", '-o', filename], stdout = subprocess.PIPE)

    def save_as(self):
        defaults = self.config['defaults']
        filename = str(self.filename_edit.text())
        abs_filename = os.path.join(defaults['save_directory'], filename)
        data = self.processed_data[self.current_image]
        for key, value in defaults['save_formats'].iteritems():
            if value:
                save_function = getattr(self, 'save_' + key)
                save_function(abs_filename, data)
        logger.debug("saving %s"%abs_filename)
        self.increment_filename()

    def increment_filename(self):
        filename = str(self.filename_edit.text())
        suffix = filename.split('_')[-1]
        prefix = filename.split('_')[:-1]
        if suffix.isdigit():
            suffix = '%02d'%(int(suffix) + 1)
            filename = '_'.join(prefix + [suffix])
        else:
            filename = '_'.join(prefix + [suffix] + ['02'])
        self.filename_edit.setText(filename)
            

    def make_temp_filename(self, suffix):
        """return (fd, filename)"""
        fd, filename = tempfile.mkstemp(suffix = suffix)
        return filename

    def save_hdf5(self, filename, data):
        import h5py
        root = h5py.File(filename + '.h5', 'w')
        tomography = root.create_dataset('tomography', data.shape, dtype = data.dtype)
        tomography[:] = data
        tomography.attrs['PixelXDimension'] = round(self.x_resolution(), 3)
        tomography.attrs['PixelYDimension'] = round(self.config['z_resolution'], 3)
        tomography.attrs['ResolutionUnit'] = 'um'
        tomography.attrs['DateTime'] = datetime.datetime.now().ctime()
        root.close()

    def save_tiff(self, filename, data):
        logger.debug('saving tiff %s'%filename)
        data = data.astype(np.float32)
        image = Image.fromstring("F" ,data.shape ,data.data, 'raw', 'F', 0 ,1)
        with open(filename + '.tiff', 'w') as fp:
            image.save(fp = fp, format = "tiff")

    def save_app_plot(self, filename, data):
        filename = filename + '.png'
        self.fig_tomography.savefig(filename, bbox_inches='tight')

    def save_serie(self, filename):
        pass

    def plot_button_released(self, event):
        if event.inaxes is self.tomography_ax:
            logger.debug("tomography axis clicked %f,%f"%(event.xdata, event.ydata))
            self.a_scan_plot_line(int(event.xdata))
        elif event.inaxes is self.a_scan_ax:
            logger.debug("a_scan axis clicked")
        else:
            logger.debug("Button released out of axes")


    def make_scale(self):
        scene_rect = self.tomography_scene.sceneRect()
        bl = scene_rect.bottomRight()
        size = QtCore.QSizeF(scene_rect.width()/4,scene_rect.height()/20)
        self.scale_rect = QRectF(bl - QtCore.QPointF(size.width()+size.height(),size.height()*2), size)
        self.scale_item = self.tomography_scene.addRect(self.scale_rect, QPen(Qt.Qt.yellow, 1), QBrush(Qt.Qt.yellow, Qt.Qt.SolidPattern))

    def remove_scale(self):
        self.tomography_scene.removeItem(self.scale_item)

    def a_scan_plot_line(self, line_index):
        self.a_scan_ax.clear()
        if self.tomography_ax.has_data():
            y = self.processed_data[self.current_image][:,line_index]
            x = np.arange(*(0,)+y.shape)
            self.a_scan_ax.plot(y, x)
            self.set_yticks(self.a_scan_ax)
            self.canvas_a_scan.draw()

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

    def setup_tomography(self):
        logger.debug("Setting tomography up")
        self.dpi = 80
        self.width = 3.4
        height = 5.3
        self.fig_tomography = plt.figure(dpi=self.dpi)
        self.canvas_tomography = FigureCanvas(self.fig_tomography)
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas_tomography)
        self.tomography_widget.setLayout(vbox)
        self.canvas_tomography.setParent(self.tomography_widget)
        self.canvas_tomography.mpl_connect('button_release_event', self.plot_button_released)
        self.zlim = [None, None]
        self.tomography_ax = plt.Axes(self.fig_tomography, [0.04, 0.05, 0.95, 0.92])
        self.fig_tomography.add_axes(self.tomography_ax)
        self.tomography_ax.plot()
        self.canvas_tomography.draw()

    def setup_a_scan(self):
        logger.debug("Setting a_scan up")
        self.dpi = 80
        self.fig_a_scan = plt.figure(dpi=self.dpi)
        self.canvas_a_scan = FigureCanvas(self.fig_a_scan)
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas_a_scan)
        self.a_scan_widget.setLayout(vbox)
        self.canvas_a_scan.setParent(self.a_scan_widget)
        self.a_scan_ax = plt.Axes(self.fig_a_scan, [0.1, 0.05, 0.85, 0.92])#, sharey = self.tomography_ax)
        self.fig_a_scan.add_axes(self.a_scan_ax)
#        self.a_scan_ax = self.fig_a_scan.add_subplot(111, sharey = self.tomography_ax)
        self.a_scan_ax.plot()
        self.a_scan_ax.invert_yaxis()
        self.canvas_a_scan.draw()

    def update_image(self, index):
        self.current_image = index
        self.plot_in_tomography_view(self.processed_data[self.current_image])
        
    def setup_camera(self):
#        self.camera_view = CameraGraphicsView()
#        self.camera_widget.addWidget(self.camera_view)
#        vbox = QVBoxLayout()
#        vbox.addWidget()
#        self.tomography_widget.setLayout(vbox)

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
        self.camera_timer.start(100)

    def change_selector(self):
        if self.d2.isChecked():
            self.scan_type = "continuous"
            self.processor.block_after_acquisition()
            self.selector = lambda start, end: self.camera_scene.addLine(QLineF(start, end), QPen(Qt.Qt.red, 1))
            self.n_images_spinbox.setEnabled(False)
            self.serie_spinbox.setEnabled(False)
        else:
            self.scan_type = "3D"
            self.processor.buffer_acquisition()
            self.selector = self.select_rect
#            self.selector = lambda start, end: self.camera_scene.addRect(QRectF(start, end))
            self.n_images_spinbox.setEnabled(True)
            self.serie_spinbox.setEnabled(True)
        logger.debug("selecting scan type %s"%self.scan_type)
        self.update_n_lines_spinbox()
        self.update_n_images_spinbox()

    def area_select(self, start, end):
        return self.camera_scene.addRect(QRectF(start, end), QPen(Qt.Qt.red, 1))

    def camera_pressed(self, event):
        self.pressed_pos = event.scenePos()
        self.camera_moved(event)

    def update_config_path(self, start, end):
        logger.debug("selecting camera scene coord %s,%s"%(str(start), str(end)))
        start = self.convert_to_path(start)
        end = self.convert_to_path(end)
        self.config[self.scan_type]['x0'] = start.x() 
        self.config[self.scan_type]['y0'] = start.y() 
        self.config[self.scan_type]['xf'] = end.x() 
        self.config[self.scan_type]['yf'] = end.y() 

    def convert_to_path(self, point):
        scale = self.config['camera_to_path_scale']
        x_offset = self.config['camera_to_path_x_offset']
        y_offset = self.config['camera_to_path_y_offset']
        offset = QPointF(x_offset, y_offset)
        transformed = (point - offset)*scale
        logger.debug("point %s"%str(transformed))
        return transformed

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
        return self.camera_scene.addRect(QRectF(start, end), QPen(Qt.Qt.red, 1))

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
        self.set_xticks(self.tomography_ax)
        self.set_yticks(self.tomography_ax)
        self.adjust_aspect_ratio()
        self.canvas_tomography.draw()

    def adjust_aspect_ratio(self):
        shape = self.current_tomography_data.shape
        length = self.current_tomography_length()*1000
        depth = self.config["z_resolution"]*shape[0]
        self.tomography_ax.set_aspect(depth/length)

    def x_resolution(self):
        length = self.current_tomography_length()
        lines = self.current_tomography_data.shape[0]
        return 1000*length/lines


    def current_tomography_length(self):
        sr = self.config[self.scan_type]
        logger.debug("current points %s"%str(sr))
        length = np.sqrt((sr['xf'] - sr['x0'])**2 + (sr['yf'] - sr['y0'])**2)
        return length

    def set_xticks(self, axes):
        shape = self.current_tomography_data.shape
        length = self.current_tomography_length()*1000
        a = float(length)/25
        b = int(np.log10(a))
        r = int(a/10**b)*10**b
        delta = int(float(r)*5)
        x_tick_labels = np.arange(0, int(length), delta)
        x_ticks_pos = x_tick_labels/length*shape[1]

        axes.set_xticks(x_ticks_pos)
        axes.set_xticklabels(x_tick_labels)

    def set_yticks(self, axes):
        shape = self.current_tomography_data.shape
        depth = self.config["z_resolution"]*shape[0]
        a = float(depth)/25
        b = int(np.log10(a))
        r = int(a/10**b)*10**b
        delta = int(float(r)*5)
        y_tick_labels = np.arange(0, int(depth), delta)
        y_ticks_pos = y_tick_labels/depth*shape[0]
        axes.set_yticks(y_ticks_pos)
        axes.set_yticklabels(y_tick_labels)

#        if hasattr(self, "tomography_item"):
#            self.tomography_scene.removeItem(self.tomography_item)
#        self.tomography_image = gray2qimage(data)
#        self.resize_tomography_view()
#        self.tomography_scene.setBackgroundBrush(QtGui.QBrush(self.tomography_image))
#        self.resize_tomography_view()
#        self.tomography_view.fitInView(self.tomography_scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def resize_tomography_view(self):
        holder_aspect_ratio = aspect_ratio(self.tomography_widget.rect())
        tomography_aspect_ratio = aspect_ratio(self.tomography_image)
        if holder_aspect_ratio > tomography_aspect_ratio:
            width = self.tomography_widget.width()
            self.tomography_view.setFixedHeight(tomography_aspect_ratio*width)
            self.tomography_view.setFixedWidth(width)
        else:
            height = self.tomography_widget.height()
            self.tomography_view.setFixedWidth(height/tomography_aspect_ratio)
            self.tomography_view.setFixedHeight(height)

    def add_data_and_update(self, data):
        logger.debug("std dev %.2e, min %.2e, max %.2e"%(np.std(data), np.min(data), np.max(data)))
        self.processed_data += [data]
        n_images = len(self.processed_data)
        self.current_image = n_images - 1
        self.select_image.setMaximum(n_images-1)
        self.select_image.setValue(self.current_image)
        if not self.lock_adjust_checkbox.isChecked():
            self.saturation_spinbox.setValue(np.average(data)+30)
            self.black_spinbox.setValue(np.average(data))

    def save_current_tomography(self):
        pass

    def start_acquisition(self):
        self.DataCollector.start()
        QObject.disconnect(self.start,SIGNAL("clicked()"),self.start_acquisition),
        QObject.connect(self.start,SIGNAL("clicked()"),self.stop_acquisition),
        self.start.setText("Stop Acquisition")
#        cmd = ["python", "doct.py", "-o", self.config['raw_file'], "--scan-single" ]
#        self.acquisition = subprocess.Popen(cmd)

    def save_serie_dialog(self):
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
    main_window.show()
    app.exec_()
