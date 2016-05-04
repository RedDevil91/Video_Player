import collections
import types
import os
import traceback
import sys
import threading
import time
os.environ["KIVY_NO_CONSOLELOG"] = "1"  # no logs will be printed to the console

from kivy.app import App
from kivy.uix.button import Button
from kivy.clock import Clock
import pyglet
from PyQt4 import QtGui, QtCore
from PySide.QtCore import Signal

_kivy_thread = None
_message_queue = collections.deque()
_message_queue_lock = threading.Lock()

if len(sys.argv) != 2:
    print("usage: %s file" % sys.argv[0])
    sys.exit(1)


class VPlayer(QtCore.QObject):

    signal = QtCore.pyqtSignal(float)

    def __init__(self):
        super(VPlayer, self).__init__()
        self.time = 0
        self.app = None

        global _kivy_thread
        _kivy_thread = threading.Thread(target=self.run)
        _kivy_thread.setDaemon(True)
        _kivy_thread.start()
        # print "THREADING!"

    def run(self):
        self.app = MyApp()
        # print threading.currentThread()
        # print "APP START!"
        self.app.run()

    def setCallback(self):
        self.app.setCallback(self.timer_print)

    def timer_print(self, time_pos):
        self.time = time_pos
        self.signal.emit(self.time)
        # print self.time  # , threading.currentThread()

    def connect_signal(self, callback):
        self.signal.connect(callback)


class MyApp(App):
    def build(self):
        from Appbase import AppBase
        self.base = AppBase(sys.argv[1])
        return self.base

    def on_start(self):
        # print "BUILD!"
        # print threading.currentThread()
        try:
            self.scheduler(0)
        except:
            print "CLOCK ERROR!"

    def setCallback(self, timecallback):
        self.base.setcallback(timecallback)

    def scheduler(self, dt):
        Clock.schedule_interval(_tend_queue, dt)


class Test(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def print_args(self):
        for a in self.args:
            print a,
        print


def _tend_queue(dt):
    # print dt
    if not _message_queue:
        # print "No task!"
        return
    else:
        while _message_queue:
            output_func, function, args, kwargs = _message_queue.popleft()
            try:
                # print function, args, kwargs, output_func
                result = function(*args, **kwargs)
            except:
                print "Caught exception in background:"
                traceback.print_exc()
                result = None
            if output_func is not None:
                # If a function to call when the output is ready was specified, do so...
                output_func(result)


class OutputContainer(object):

    def __init__(self):
        self.value = None
        self.filled = False

    def __call__(self, value):
        self.value = value
        self.filled = True


def _call_pyglet_function(function, args, kwargs, output_func):
    # basic core of calling a function
    if _kivy_thread is None:
        _message_queue.append((output_func, function, args, kwargs))
    else:
        _message_queue_lock.acquire()
        _message_queue.append((output_func, function, args, kwargs))
        _message_queue_lock.release()


def call_pyglet_function(function, args=[], kwargs={}, return_result=True):
    """Call a function from within the pyglet background thread safely.
    If return_result is True, the output of the function will be returned,
    otherwise it will be discarded, which is slightly faster."""
    try:
        return_result = kwargs['return_result']
    except KeyError:
        pass
    if return_result:
        output = OutputContainer()
    else:
        output = None
    _call_pyglet_function(function, args, kwargs, output)
    # _tend_queue(-1)
    if return_result:
        while not output.filled:
            # Just spin waiting for the result to be appended to the output list.
            pass
        return output.value


class PygletProxy(object):
    """Thread-safe proxy for a pyglet object. Pass the constructor a class object
    and provide the required arguments for initializing that class.
    The required instance will then be constructed in the pyglet background thread.
    The instance can be interacted with transparently through this proxy: getting
    and setting attributes and calling functions is done in a thread-safe manner
    by message passing. In addition, the object's dict is proxied, so dir()
    and friends works properly too.

    Example:
    win = PygletProxy(my_background_window, width=600, height=200)
    win.width = 500
    print dir(win)
    win.close()
    """
    class_names = {'__init__', '__getattribute__', '__setattr__', '_proxy_object'}

    def __init__(self, object_class, *args, **kwargs):
        # ask the pyglet thread to make us the required object; however don't wait for it...
        # The thread could be blocked (e.g. if we try to construct such a proxy during
        # a module import), so we'll just let the proxy reference be filled in
        # when it's ready.
        object.__setattr__(self, '_proxy_object', None)
        output_func = lambda result: object.__setattr__(self, '_proxy_object', result)
        _call_pyglet_function(object_class, args, kwargs, output_func)

    def __getattribute__(self, name):
        if name in PygletProxy.class_names:
            return object.__getattribute__(self, name)
        while self._proxy_object is None:
            pass  # wait for the object to be ready if not yet created
        value = getattr(self._proxy_object, name)
        if isinstance(value, types.MethodType):
            return ProxyFunction(value)
        else:
            return value

    def __setattr__(self, name, value):
        while self._proxy_object is None:
            pass  # wait for the object to be ready if not yet created
        if hasattr(self._proxy_object, name):
            call_pyglet_function(setattr, (self._proxy_object, name, value), {}, return_result=False)
        else:
            object.__setattr__(self, name, value)


class ProxyFunction(object):
    def __init__(self, function):
        self.function = function

    def __call__(self, *args, **kwargs):
        return call_pyglet_function(self.function, args, kwargs)


class Example(QtGui.QWidget):
    def __init__(self, player):
        super(Example, self).__init__()
        self.player = player
        self.initUI()

    def initUI(self):
        qbtn = QtGui.QPushButton('Quit', self)
        qbtn.clicked.connect(QtCore.QCoreApplication.instance().quit)
        qbtn.resize(qbtn.sizeHint())
        qbtn.move(50, 50)

        self.lcd = QtGui.QLCDNumber(self)
        # lcd.display(19)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(qbtn)
        vbox.addWidget(self.lcd)

        self.setLayout(vbox)

        try:
            self.player.connect_signal(self.displayTime)
            # self.player.signal.connect(self.displayTime)
        except:
            print "ERROR!!!"

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Quit button')
        self.show()

    def displayTime(self, time):
        self.lcd.display(time)


def main():
    vplayer.setCallback()
    app = QtGui.QApplication(sys.argv)
    ex = Example(vplayer)
    sys.exit(app.exec_())


# pyglet.clock.schedule_interval(_tend_queue, 0.1)
# Clock.schedule_interval(_tend_queue, 0.01)
# test = PygletProxy(Test, 1, 2, 3, 4, test1=True, test2=False)
# _tend_queue(0)
# test2 = PygletProxy(MyApp)
# _tend_queue(1)
# test2.run()
vplayer = PygletProxy(VPlayer)
_tend_queue(0)
# vplayer.setCallback(return_result=False)
# vplayer.setCallback()
# print _message_queue
print "START!"
main()
print "END"
# print test._proxy_object
# print test.args
# print test.print_args()
# Clock.unschedule(_tend_queue)'''
# pyglet.clock.unschedule(_tend_queue)
