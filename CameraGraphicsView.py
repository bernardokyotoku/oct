from PyQt4 import QtGui

class CameraGraphicsView(QtGui.QGraphicsView):
    def __init__(self, *args):
        super(CameraGraphicsView, self).__init__(*args)
        
    def sizeHint(self):
        size = self.size()
        size.setWidth(size.height()*4./3.)
        return size

    def closeEvent(self, event):
        print "closing"
        self.camera_timer.stop()
        self.camera_device.StopLiveVideo()
        self.camera_device.FreeImageMem()
        self.camera_device.ExitCamera()
