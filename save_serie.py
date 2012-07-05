#!/usr/bin/env python
import sys
import gobject, pygst
pygst.require('0.10')
from configobj import ConfigObj
from PyQt4 import QtCore, QtGui, uic
#from PyQt4.QtGui import QAction, QMainWindow, QWidget, QApplication, qApp, QIcon, QTextEdit, QMenu, QGridLayout, QPushButton, QGraphicsView, QGraphicsScene, qBlue, QPen, QRadioButton, QGroupBox, QButtonGroup, QPixmap, QSizePolicy, QPainter, QFont, QFrame, QPallete
from PyQt4.QtGui import *
from PyQt4.QtCore import QLine, QString, QObject, SIGNAL, QLineF, QRectF, QRect, QPoint, QPointF
form_class, base_class = uic.loadUiType("save_series.ui")
from PyQt4 import Qt

class SaveSerieDialog(QtGui.QDialog, form_class):
    def __init__(self,parent = None, selected = [], flag = 0, *args):
        QtGui.QWidget.__init__(self, parent, *args)
        self.setupUi(self)
        self.config = pro.parse_config()

    def fill_save_path(self):
        filename = QtGui.QFileDialog.getOpenFileName()
        self.save_file_path.setText(filename)
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main_window = SaveSerieDialog()
    main_window.show()
    app.exec_()
