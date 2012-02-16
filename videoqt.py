import gobject, pygst
pygst.require('0.10')
import gst
from PyQt4.QtGui import QMainWindow, QWidget, QApplication 
import sys

class Video(QMainWindow):
	    def __init__(self):
        QMainWindow.__init__(self)
        container = QWidget()
        self.setCentralWidget(container)
        self.windowId = container.winId()
        self.setGeometry(300,300,640,480)
        self.show()

    def setUpGst(self):
        self.player = gst.Pipeline("player")
        source = gst.element_factory_make("v4l2src", "vsource")
        sink = gst.element_factory_make("xvimagesink", "sink")
        fvidscale_cap = gst.element_factory_make("capsfilter", "fvidscale_cap")
        fvidscale = gst.element_factory_make("videoscale", "fvidscale")
        caps = gst.caps_from_string('video/x-raw-yuv')
        fvidscale_cap.set_property('caps', caps)
        source.set_property("device", "/dev/video0")

        self.player.add(source, fvidscale, fvidscale_cap, sink)
        gst.element_link_many(source,fvidscale, fvidscale_cap, sink)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
            print "end of message"
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
            imagesink.set_xwindow_id(win_id)

    def startPrev(self):
        self.player.set_state(gst.STATE_PLAYING)
        print "should be playing"

if __name__ == "__main__":
    gobject.threads_init()
    app = QApplication(sys.argv)
    video = Video()
    video.setUpGst()
    video.startPrev()
    sys.exit(app.exec_())
