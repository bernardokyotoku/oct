#!/usr/bin/env python
import gobject
import sys
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import *
from PyQt4.QtCore import QLine, QString, QObject, SIGNAL, QLineF, QRectF, QRect, QPoint, QPointF
form_class, base_class = uic.loadUiType("testui.ui")
from PyQt4 import Qt

class OCT (QtGui.QMainWindow, form_class):
    def __init__(self,parent = None, selected = [], flag = 0, *args):
        QtGui.QWidget.__init__(self, parent, *args)
        self.setupUi(self)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main_window = OCT()
    main_window.show()
    app.exec_()
