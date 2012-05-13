from PyQt4 import QtGui

class CameraGraphicsView(QtGui.QGraphicsView):
    def __init__(self, *args):
        super(CameraGraphicsView, self).__init__(*args)
        
    def sizeHint(self):
        size = self.size()
        size.setWidth(size.height()*4/3)
        return size
