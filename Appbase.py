import sys
import collections
import numpy as np
from kivy.uix.videoplayer import VideoPlayer
from kivy.core.window import Window
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock


class AppBase(RelativeLayout):
    def __init__(self, filename, **kwargs):
        super(AppBase, self).__init__(**kwargs)
        self.padding = 20

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        self.v = VideoPlayer(source=filename, state='stop')
        self.add_widget(self.v)

        self.label = Label()
        self.label.pos_hint = {'center_x': .8, 'center_y': .8}
        self.label.color = (0, 255, 0, 1)
        self.label.font_size = '30sp'
        self.add_widget(self.label)
        self.rect_label = None

        self.rect = None
        self.value = 0.0

        self.last_position = None
        self.frameGaps = collections.deque([0.1], maxlen=10)
        self.framegap = 0.0
        self.updated = False
        self.customspeed = False
        self.speed = 2.0

        self.draw_rect = False
        self.bind(pos=self.on_resize, size=self.on_resize)

    def _keyboard_closed(self):
        print('My keyboard have been closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print 'The key', keycode[1], 'have been pressed'
        # print(' - text is %r' % text)
        # print(' - modifiers are %r' % modifiers)

        if keycode[1] == 'h':
            self.draw_rect = True
        elif keycode[1] == 'g':
            self.draw_rect = False
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
        elif keycode[1] == 'pageup':
            if self.speed < 16.0:
                self.speed *= 2.0
                if self.speed == 1.0:
                    self.speed = 2.0
        elif keycode[1] == 'pagedown':
            if self.speed > 1.0 / 16.0:
                self.speed /= 2.0
                if self.speed == 1.0:
                    self.speed = 0.5
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
            Clock.schedule_interval(self.update, 0.0)  # Schedule at max interval (once per frame)
            self.label.text = 'Play >'

    def custom_play_pause(self):
        if self.v.state == 'play':
            self.play_pause()
        if self.customspeed is False:
            self.customspeed = True
            Clock.schedule_interval(self.custom_update, 0.0)
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

    def on_draw(self):
        if self.rect is None and self.draw_rect:
            with self.canvas:
                Color(1, 0, 0, 0.3, mode='rgba')
                self.rect = Rectangle(pos=(self.padding, self.padding),
                                      size=(self.width - 2 * self.padding, self.height - 2 * self.padding))
                self.rect_label = Label(pos_hint={'center_x': .5, 'center_y': .5},
                                        text='Objects',
                                        font_size='50sp',
                                        color=(1,1,1,1))
                self.add_widget(self.rect_label)
        if self.rect is not None and not self.draw_rect:
            self.canvas.remove(self.rect)
            self.rect_label.text = ''
            self.rect = None
            # self.canvas.clear()

        # print self.rect_label is None

    def on_resize(self, *args):
        if self.rect is not None:
            self.rect.pos = (self.padding, self.padding)
            self.rect.size = (self.width - 2 * self.padding, self.height - 2 * self.padding)

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
        self.tick()
        self.on_draw()

    def custom_update(self, dt):
        # TODO check video position and start normal play when position is close to eos
        self._frameGap()
        self.step_video(True, step_size=self.framegap * self.speed)
        if self.speed > 1:
            self.label.text = 'Custom speed x %d ' % int(self.speed)
        else:
            self.label.text = 'Custom speed x 1/%d ' % int(1/self.speed)
        self.on_draw()