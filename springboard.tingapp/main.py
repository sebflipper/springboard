import tingbot
from threading import Timer
from settings import Settings
from tingbot import *
from tingapp import TingApp
from cached_property import cached_property
import os, logging, math, subprocess, json

from icon_utils import iconise, get_network_icon_name

class PeripheralFinder():
    def __init__(self, delay=0.5):
        self.stopping = False
        self.mouse_attached = False
        self.keyboard_attached = False
        self.joystick_attached = False
        self.network_icon = 'WiFi-1.png'
        Timer(delay, self.find_peripherals).start()

    def find_peripherals(self):  # all off these assignments are atomic, so are thread safe.
        if not self.stopping:
            self.mouse_attached = mouse_attached()
            self.keyboard_attached = keyboard_attached()
            self.joystick_attached = joystick_attached()
            self.network_icon = get_network_icon_name(get_wifi_cell())
            Timer(0.5, self.find_peripherals).start()

    def stop(self):
        self.stopping = True

apps_dir = os.environ.get('APPS_DIR', '/apps')
apps = []

for filename in os.listdir(apps_dir):
    file = os.path.join(apps_dir, filename)
    _, ext = os.path.splitext(file)

    if ext == '.tingapp':
        apps.append(TingApp(file))

state = {
    'app_index': 0,
    'scroll_position': 0,
}

@left_button.press
def button_left():
    state['app_index'] -= 1
    if state['app_index'] < 0:
        state['app_index'] = 0
        state['scroll_position'] -= 0.02  # little nudge animation

@right_button.press
def button_right():
    state['app_index'] += 1
    if state['app_index'] >= len(apps):
        state['app_index'] = len(apps) - 1
        state['scroll_position'] += 0.02  # little nudge animation


@touch(size=(320, 70), align="top")
def on_show_settings(action):
    if action == 'down':
        # get the color of the screen currently
        color = background_color(state['scroll_position'])
        # darken that by 40%
        color = tuple(c*0.6 for c in color)
        # run the settings pane modally
        Settings(background_color=color).run()

@touch(size=(320, 240-70), align="bottom")
def on_touch(action):
    if action == 'down':
        app = apps[state['app_index']]
        screen.fill(color='black')
        screen.text(
            'Opening %s...' % os.path.basename(app.path),
            font_size=14,
            color='white')

        screen.update()
        subprocess.check_call(['tbopen', os.path.abspath(app.path)])

def draw_app_at_index(app_i, scroll_position):
    if app_i < 0 or app_i >= len(apps):
        return

    draw_x = -(scroll_position - app_i)*320 + 160
    app = apps[int(app_i)]
    app.draw(surface=screen, centered_at=(draw_x, 102))

dot_selected_image = Image.load('dot-selected.png')
dot_image = Image.load('dot.png')

def draw_dots():
    num_apps = len(apps)

    width = num_apps * 10
    start_x = 320/2 - width/2

    for app_i in range(len(apps)):
        if app_i == state['app_index']:
            image = dot_selected_image
        else:
            image = dot_image

        screen.image(
            image,
            xy=(start_x + app_i*10, 227),
            align='left'
        )

def background_color(scroll_position):
    left_i = int(math.floor(scroll_position))
    right_i = int(math.ceil(scroll_position))

    # clamp these indicies to be within the bounds of the list
    left_i = max(left_i, 0)
    right_i = max(right_i, 0)
    left_i = min(left_i, len(apps) - 1)
    right_i = min(right_i, len(apps) - 1)

    left_color = apps[left_i].background_color
    right_color = apps[right_i].background_color

    if left_i == right_i:
        return left_color

    left_amount = 1 - (scroll_position - left_i)
    right_amount = 1 - (right_i - scroll_position)

    color = (
        left_color[0] * left_amount + right_color[0] * right_amount,
        left_color[1] * left_amount + right_color[1] * right_amount,
        left_color[2] * left_amount + right_color[2] * right_amount,
    )

    return color

def loop():
    scroll_position = state['scroll_position']
    app_index = state['app_index']

    screen.fill(color=background_color(scroll_position))

    screen.image(
        'tingbot-t.png',
        xy=(10, 7),
        align='topleft',
    )
    if finder.mouse_attached:
        mouse_img = 'Mouse-1.png'
    else:
        mouse_img = 'Mouse-2.png'
    if finder.keyboard_attached:
        kbd_img = 'Keyboard-1.png'
    else:
        kbd_img = 'Keyboard-2.png'
    if finder.joystick_attached:
        joystick_img = 'Gamepad-1.png'
    else:
        joystick_img = 'Gamepad-2.png'
    screen.image(iconise(finder.network_icon), xy=(300, 6), align='top')
    screen.image(iconise(joystick_img), xy=(289, 6), align='topright')
    screen.image(iconise(mouse_img), xy=(268, 6), align='topright')
    screen.image(iconise(kbd_img), xy=(257, 6), align='topright')
    draw_dots()

    scroll_position += (app_index-scroll_position)*0.2

    if math.floor(scroll_position) != math.ceil(scroll_position):
        draw_app_at_index(
            int(math.floor(scroll_position)),
            scroll_position)

    draw_app_at_index(
        int(math.ceil(scroll_position)),
        scroll_position)

    state['scroll_position'] = scroll_position

# run the app
finder = PeripheralFinder(1.0)
try:
    tingbot.run(loop)
finally:
    finder.stop()
