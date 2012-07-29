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
save_option_dialog_form, base_class = uic.loadUiType("save_option_dialog.ui")
from PyQt4 import Qt

class SaveSerieDialog(QtGui.QDialog, form_class):
    def __init__(self,parent = None, selected = [], flag = 0, *args):
        QtGui.QWidget.__init__(self, parent, *args)
        self.setupUi(self)

    def fill_save_path(self):
        filename = QtGui.QFileDialog.getOpenFileName()
        self.save_file_path.setText(filename)

class SaveOptionDialog(QtGui.QDialog, save_option_dialog_form):
    def __init__(self, parent = None, selected = [], flag = 0, *args):
        QtGui.QWidget.__init__(self, parent, *args)
        self.parent = parent
        self.setupUi(self)
        self.dir_path_edit.setText(self.parent.config['defaults']['save_directory'])
        for key, value in self.parent.config['defaults']['save_formats'].iteritems():
            checkbox = getattr(self, key+'_checkbox')
            checkbox.setChecked(value)

    def fill_dir_path_edit(self):
        filename = QtGui.QFileDialog.getExistingDirectory()
        self.dir_path_edit.setText(filename)
        
    def accept(self):
        defaults = self.parent.config['defaults']
        if self.parent is not None:
            defaults['save_directory'] = str(self.dir_path_edit.text())
            for key, value in defaults['save_formats'].iteritems():
                checkbox = getattr(self, key+'_checkbox')
                defaults['save_formats'][key] = checkbox.isChecked()
        self.close()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main_window = SaveOptionDialog()
    main_window.show()
    app.exec_()
