#!/usr/bin/python
from PyQt4 import QtGui 
from PyQt4.QtGui import QAction, QMainWindow, QWidget, QApplication, qApp, QIcon, QTextEdit, QMenu, QGridLayout, QPushButton, QGraphicsView, QGraphicsScene, qBlue, QPen, QRadioButton, QGroupBox, QButtonGroup, QPixmap
from PyQt4.QtCore import QLine, QString
import sys

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
		self.initUI()

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

	def makeMenus(self):
		menuBar = self.menuBar()
		menuFile = menuBar.addMenu('File')
		menuEdit = menuBar.addMenu('Edit')
		menuFile.addAction(self.exitAction)

	def makeRightPane(self):
		buttonQuit = QPushButton('hello')
		self.camera_view = QGraphicsView(CameraScene())
		pane_scan_type = self.makeScanTypeButtons()

		pane_right = QWidget()
		grid_right = QGridLayout()
		grid_right.addWidget(buttonQuit,0,0)
		grid_right.addWidget(pane_scan_type,1,0)
		grid_right.addWidget(self.camera_view,2,0)
		pane_right.setLayout(grid_right)
		return pane_right

	def setUpGst(self):
		self.player = gst.Pipeline("player")
		source = gst.element_factory_make("v4l2src", "vsource")
		sink = gst.element_factory_make("autovideosink", "outsink")
		source.set_property("device", "/dev/video0")
		scaler = gst.element_factory_make("videoscale", "vscale")
		self.window_id = None

		self.player.add(source, scaler, sink)
		gst.element_link_many(source, scaler, sink)
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.enable_sync_message_emission()
		bus.connect("message", self.on_message)
		bus.connect("sync-message::element", self.on_sync_message)
		
	def on_message(self, bus, message):
		t = message.type
		if t == gst.MESSAGE_EOS:
			self.player.set_state(gst.STATE_NULL)
		elif t == gst.MESSAGE_ERROR:
			err, debug = message.parse_error()
			print "Error: %s" % err, debug
			self.player.set_state(gst.STATE_NULL)

	def on_sync_message(self, bus, message):
		if message.structure is None:
			return
		message_name = message.structure.get_name()
		if message_name == "prepare-xwindow-id":
			win_id = self.windowId
			assert win_id
			imagesink = message.src
			imagesink.set_property("force-aspect-ratio", True)
			imagesink.set_xwindow_id(win_id)

	def startPrev(self):
		self.player.set_state(gst.STATE_PLAYING)
		print "should be playing"

	def makeLeftPane(self):
		self.tomography_view = QGraphicsView(QGraphicsScene())
		self.plot_view = QGraphicsView(QGraphicsScene())
		wd = QWidget()
		self.WindowId = wd.WinId()
		self.tomography_view.scene().addWidget(wd)


		pane_left = QWidget()
		grid_left = QGridLayout()
		grid_left.addWidget(self.plot_view,0,0)
		grid_left.addWidget(self.tomography_view,0,1)
		grid_left.setColumnStretch(1,2)
		pane_left.setLayout(grid_left)
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

		

def main():
	app = QtGui.QApplication(sys.argv)
	ex = OCT()
	#ex.tomography_view.scene().addPixmap(QPixmap("CNH.jpg"))
	ex.tomography_view.scene().addWidget(wd)
	tomography = ex.tomography_view
	tomography.wheelEvent = getZoom(tomography)

	sys.exit(app.exec_())

if __name__ == "__main__":
	main()
   
