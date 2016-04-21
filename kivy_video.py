import sys
import collections
import numpy as np
from kivy.app import App
from kivy.uix.videoplayer import VideoPlayer
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.video import Video
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.properties import *
from kivy.clock import Clock


if len(sys.argv) != 2:
    print("usage: %s file" % sys.argv[0])
    sys.exit(1)


class AppBase(RelativeLayout):
    def __init__(self, **kwargs):
        super(AppBase, self).__init__(**kwargs)
        self.pos = (0, 0)

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        self.v = VideoPlayer(source=sys.argv[1], state='stop')
        self.add_widget(self.v)

        self.label = Label()
        self.label.color = (0, 255, 0, 1)
        self.label.pos_hint = {'top': 1.4, 'right': 1.3}
        self.label.font_size = '30sp'
        self.add_widget(self.label)

        self.rect = None
        self.customspeed = False
        self.value = 0.0

        self.last_position = None
        self.frameGaps = collections.deque([0.1], maxlen=10)
        self.framegap = 0.0
        self.updated = False

    def _keyboard_closed(self):
        print('My keyboard have been closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print 'The key', keycode[1], 'have been pressed'
        # print(' - text is %r' % text)
        # print(' - modifiers are %r' % modifiers)

        if keycode[1] == 'h':
            self.draw_rect()
        elif keycode[1] == 'g':
            self.clear_canvas()
        elif keycode[1] == 's':
            self.custom_play_pause()
        elif keycode[1] == 'left':
            self.v.state = 'pause'
            self.step_video(False)
            self.label.text = "<< Step backward"
        elif keycode[1] == 'right':
            self.v.state = 'pause'
            self.step_video(True)
            self.label.text = "Step forward >>"
        elif keycode[1] == 'spacebar':
            self.play_pause()
        elif keycode[1] == 'enter':
            self.v.state = 'stop'
            self.v.seek(0.0)
            self.label.text = ''
        elif keycode[1] == 'escape':
            sys.exit(1)

        # Return True to accept the key. Otherwise, it will be used by
        # the system.
        return True

    def play_pause(self):
        if self.customspeed:
            self.custom_play_pause()
        if self.v.state == 'play':
            self.v.state = 'pause'
            Clock.unschedule(self.update)
            self.label.text = 'Pause ||'
        else:
            self.v.state = 'play'
            Clock.schedule_interval(self.update, 0.0)  #Schedule at max interval
            self.label.text = 'Play >'


    def custom_play_pause(self):
        if self.v.state == 'play':
            self.play_pause()
        if self.customspeed is False:
            self.customspeed = True
            Clock.schedule_interval(self.custom_update, 0.0)
            self.label.text = 'Custom speed >>'
        else:
            self.customspeed = False
            Clock.unschedule(self.custom_update)
            self.label.text = 'Pause ||'

    def step_video(self, direction, step_size=0.05):
        if direction:
            self.value = (self.v.position + step_size) / self.v.duration
        else:
            self.value = (self.v.position - step_size) / self.v.duration
        self.v.seek(self.value)

    def draw_rect(self):
        if self.rect is None:
            with self.canvas:
                Color(1, 0, 0, 0.5, mode='rgba')
                self.rect = Rectangle(pos_hint={'top': 1, 'right': 1}, size=(100, 100))

    def clear_canvas(self):
        if self.rect is not None:
            self.canvas.remove(self.rect)
            self.rect = None
            #self.canvas.clear()

    def tick(self):
        if self.last_position is None:
            self.last_position = self.v.position
        else:
            if self.v.position > self.last_position:
                self.frameGaps.append(self.v.position - self.last_position)
                self.last_position = self.v.position
                self.updated = True

    def _frameGap(self):
        if self.updated:
            self.framegap = np.mean(self.frameGaps)
            self.updated = False

    def update(self, dt):
        print dt
        self.tick()

    def custom_update(self, dt):
        self._frameGap()
        self.step_video(True, step_size=self.framegap * 4)


class MyApp(App):
    def build(self):
        return AppBase()

MyApp().run()
