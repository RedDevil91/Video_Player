import sys
import os

# os.environ["KIVY_NO_CONSOLELOG"] = "1"  # no logs will be printed to the console

import threading
import time
from kivy.app import App


if len(sys.argv) != 2:
    print("usage: %s file" % sys.argv[0])
    sys.exit(1)


class MyApp(App):
    def build(self):
        from Appbase import AppBase
        base = AppBase(sys.argv[1])
        return base


def run_app():
    app = MyApp()
    app.run()

if __name__ == '__main__':
    # run_app()
    back_thread = threading.Thread(target=run_app)
    back_thread.setDaemon(True)
    back_thread.start()
    # back_thread.run()
    print
    print "!"
    print
    timer = 0
    prev_time = time.time()
    while timer < 30:
        next_time = time.time()
        timer += next_time - prev_time
        prev_time = next_time
