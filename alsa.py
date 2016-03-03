import alsaaudio
import audioop
import math
import logging
import threading
import time

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')

from gi.repository import GObject, Gdk, Gio, Gtk


class ClickDetecter(object):
    def __init__(self):
        self._inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)
        self._inp.setchannels(1)
        self._inp.setrate(8000)
        self._inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self._inp.setperiodsize(160)

    def wait_for_click(self, timeout=3.):
        blipp = time.time()
        for i in range(30):
            l, data = self._inp.read()
        while True:
            # Read data from device
            l, data = self._inp.read()
            if (time.time() - blipp) > (timeout + 0.21):
                return (time.time() - blipp) / timeout * 100
            if l:
                spike = audioop.max(data, 2)
                #print repr(spike)
                if spike > 32000:
                    return (time.time() - blipp) / timeout * 100
            time.sleep(.001)


class Application(object):
    def __init__(self):
        self.progress = 0
        self.ready = False
        self._keep_running = False
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

        self.init_iu()

    def init_iu(self):
        self.darea = Gtk.DrawingArea()
        self.darea.connect("draw", self.expose)

        self._window = Gtk.Window(title='asdf')
        self._window.add(self.darea)
        self._window.connect("delete-event", self.main_quit)
        #self._window.fullscreen()
        self._window.resize(600, 600)
        self._window.show_all()

    def expose(self, wid, cr):
        w, h = self._window.get_size()

        if self.ready:
            cr.set_source_rgb(0.1, 0.6, 0.9)
            cr.rectangle(20, 20, 20, 20)
            cr.fill()

        # Draw aim
        if self.progress == 0:
            cr.set_source_rgb(0.6, 0.6, 0.6)
        elif self.progress < 60:
            cr.set_source_rgb(0.9, 0.9, 0.1)
        elif self.progress > 100:
            cr.set_source_rgb(0.9, 0.3, 0.1)
        else:
            cr.set_source_rgb(0.2, 0.7, 0.3)

        cr.arc(w/2, (h-150)/2, (h-180)/2, 0, 2*math.pi)
        cr.fill()

        # Set progress
        if self.progress > 0:
            cr.set_line_width(6)
            cr.set_source_rgb(0.1, 0.1, 0.1)
            cr.rectangle(100, h-120, (w-100-100) / 100. * self.progress, 80)
            cr.stroke_preserve()

            if self.progress < 60:
                cr.set_source_rgb(0.9, 0.9, 0.1)
            elif self.progress > 100:
                cr.set_source_rgb(0.9, 0.3, 0.1)
            else:
                cr.set_source_rgb(0.2, 0.7, 0.3)
            cr.fill()

        # Add bar outline
        cr.set_line_width(6)
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.rectangle(100, h-120, w-100-100, 80)
        cr.stroke_preserve()

    def run(self):
        detector = ClickDetecter()

        self._keep_running = True
        while self._keep_running:
            print "Klar"
            self.progress = 0
            self.ready = True
            self._window.queue_draw()

            time.sleep(5)
            self.ready = False
            self._window.queue_draw()

            print "Waiting for click"
            b = detector.wait_for_click(3)
            print b
            if b > 120:
                self.progress = 120
            else:
                self.progress = b
            self._window.queue_draw()
            time.sleep(1)

    def main(self):
        logging.info("Starting packing application")
        GObject.threads_init()  # Allow background threads
        Gtk.main()              # Run application

    def main_quit(self, *args):
        Gtk.main_quit(*args)
        print "stopping"
        self._keep_running = False
        raise SystemExit(1)
        #self.thread.join()


if __name__ == "__main__":
    Application().main()
