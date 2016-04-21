import sys
from kivy.app import App
from kivy.uix.videoplayer import VideoPlayer
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.video import Video
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.properties import *

if len(sys.argv) != 2:
    print("usage: %s file" % sys.argv[0])
    sys.exit(1)


class AppBase(FloatLayout):
    def __init__(self, **kwargs):
        super(AppBase, self).__init__(**kwargs)

        self._keyboard = Window.request_keyboard(self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        self.v = VideoPlayer(source=sys.argv[1], state='play')
        self.add_widget(self.v)
        self.value = 0.0

        self.label = Label()
        self.label.pos = (-280, -200)
        self.label.color = (0, 255, 0, 1)
        self.label.font_size = '30sp'
        self.add_widget(self.label)

        self.rect = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print('The key', keycode, 'have been pressed')
        print(' - text is %r' % text)
        print(' - modifiers are %r' % modifiers)

        if keycode[1] == 's':
            self.value += 0.1
            if self.value >= 1:
                self.value = 0.0
            self.v.seek(self.value)
        elif keycode[1] == 'h':
            self.draw_rect()
        elif keycode[1] == 'g':
            self.clear_canvas()
        elif keycode[1] == 'left':
            print self.v.duration
        elif keycode[1] == 'right':
            print self.v.position
        elif keycode[1] == 'spacebar':
            if self.v.state == 'play':
                self.v.state = 'pause'
            else:
                self.v.state = 'play'
        elif keycode[1] == 'enter':
            self.v.state = 'stop'
            self.v.seek(0.0)
        elif keycode[1] == 'escape':
            sys.exit(1)

        self.label.text = self.v.state
        # Return True to accept the key. Otherwise, it will be used by
        # the system.
        return True

    def draw_rect(self):
        if self.rect is None:
            with self.canvas:
                Color(1, 0, 0, 0.5, mode='rgba')
                self.rect = Rectangle(pos=(200, 200), size=(200, 200))

    def clear_canvas(self):
        if self.rect is not None:
            self.canvas.remove(self.rect)
            self.rect = None
            #self.canvas.clear()


class MyApp(App):
    def build(self):
        return AppBase()

MyApp().run()
