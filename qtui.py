#!/usr/bin/python
 
import sys
from PyQt4 import QtGui 
from PyQt4.QtGui import QAction, QMainWindow, QWidget, QApplication, qApp, QIcon, QTextEdit, QMenu, QGridLayout, QPushButton, QGraphicsView, QGraphicsScene, qBlue, QPen
from PyQt4.QtCore import QLine

class CameraScene(QGraphicsScene):
	def __init__(self):
		super(CameraScene, self).__init__()
		self.start_point = None
		self.x1 = None
		self.y1 = None
		self.selection_type = 1
		self.setSceneRect(0,0,100,100)

	def mousePressEvent(self,event):
		self.start_point = event.scenePos()
		self.x1 = self.start_point.x()
		self.y1 = self.start_point.y()

	def mouseMoveEvent(self,event):
		map(self.removeItem,self.items())
		x2 = event.scenePos().x()
		y2 = event.scenePos().y()
		def rect(x1,y1,x2,y2):
			width = x2-x1	
			height = y2-y1
			x = (x2,-width) if width < 0 else (x1,width)
			y = (y2,-height) if height < 0 else (y1,height)
			self.addRect(x[0],y[0],x[1],y[1])
		select = [self.addLine,rect][self.selection_type]
		select(self.x1,self.y1,x2,y2)

class Example(QMainWindow):
	def __init__(self):
		super(Example, self).__init__()
		self.initUI()

	def initUI(self):
		container = QWidget()
		self.setCentralWidget(container)
		exitAction = QAction('Exit',self)
		exitAction.setShortcut('Ctrl+Q')
		exitAction.setStatusTip('Exit application')
		exitAction.triggered.connect(qApp.quit)

		menuBar = self.menuBar()
		menuFile = menuBar.addMenu('File')
		menuEdit = menuBar.addMenu('Edit')
		menuFile.addAction(exitAction)

		textEdit = QTextEdit()
		buttonQuit = QPushButton('hello')
		self.camera_view = QGraphicsView(CameraScene())

		pane_right = QWidget()
		grid_right = QGridLayout()
		grid_right.addWidget(buttonQuit,0,0)
		grid_right.addWidget(self.camera_view,1,0)
		pane_right.setLayout(grid_right)

		grid = QGridLayout()
		grid.addWidget(textEdit,0,0)
		grid.addWidget(pane_right,0,1)
		container.setLayout(grid)

#		scene = QGraphicsScene()
#		scene.addLine(0,0,10,10)
#		self.camera_view.setScene(scene)

		self.setGeometry(300,300,250,150)
		self.show()

		def mousePress(event):
			self.statusBar().showMessage(str(event.pos()))
		
		#self.camera_view.mousePressEvent = mousePress

		self.setGeometry(300,300,250,150)
		self.statusBar().showMessage("Ready")
		self.setWindowTitle("OCT")
		self.show()

		

def main():
	app = QtGui.QApplication(sys.argv)
	ex = Example()

	sys.exit(app.exec_())

if __name__ == "__main__":
	main()
   
