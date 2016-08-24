import socket
import threading
import subprocess
import re
import math

import wifi
import pygame
import tingbot
import tingbot_gui as gui
from icon_utils import get_network_icon_name, iconise

IFACE = 'wlan0'

default_style = gui.get_default_style()

default_style.button_text_font = "OpenSans-Semibold.ttf"
default_style.statictext_font = "OpenSans-Semibold.ttf"
default_style.statictext_font_size = 14
default_style.button_text_font_size = 14
default_style.button_pressed_color = (255, 255, 255, 100)
default_style.button_color = (255, 255, 255)
default_style.popup_bg_color = (255, 255, 255, 50)

def draw_cell(widget, cell):
    if widget.pressed:
        widget.fill(widget.style.button_pressed_color)
    else:
        widget.fill(widget.style.popup_bg_color)
    if hasattr(cell, 'ssid'):
        label = cell.ssid
        widget.image(iconise(get_network_icon_name(cell)),
                     xy=(widget.size[0]-5, widget.size[1] / 2),
                     align="right")
        if hasattr(cell, 'encrypted') and cell.encrypted:
            widget.image(iconise("Lock-1.png"),
                         xy=(widget.size[0]-23, widget.size[1] / 2),
                         align="right")
    else:
        label = cell
    widget.text(label,
                xy=(5, widget.size[1] / 2),
                size=(widget.size[0]-36, widget.size[1]),
                align="left",
                color=widget.style.button_text_color,
                font=widget.style.button_text_font,
                font_size=widget.style.button_text_font_size)


class CellButton(gui.Button):
    def draw(self):
        draw_cell(self, self.label)


class CellDropDown(gui.DropDown):
    def __init__(self, *args, **kwargs):
        super(CellDropDown, self).__init__(*args, **kwargs)
        self.style.popupmenu_button_class = CellButton

    def draw(self):
        draw_cell(self, self.selected[0])


class CellSettings(gui.MessageBox):
    def __init__(self, cell, style=None):
        super(CellSettings, self).__init__((20, 20), (280, 160), "topleft", style=style,
                                           buttons=['Connect', 'Forget', 'Cancel'])
        gui.StaticText((140, 0), (100, 30), "top", parent=self.panel, label=cell.ssid)
        self.cell = cell
        self.scheme = wifi.Scheme.find(IFACE, cell.ssid)
        if cell.encrypted:
            if self.scheme:
                pwd = "        "
            else:
                pwd = ""
            gui.StaticText((10, 55), (90, 30), "left", label="Password:",
                           style=style, parent=self.panel)
            self.password = gui.PasswordEntry((270, 55), (160, 30), "right", parent=self.panel,
                                              label="Password", string=pwd)
        else:
            self.password = None

    def close(self, label):
        if label == "Connect":
            if (self.scheme is None) or (self.password and self.password.string != "        "):
                if self.scheme:
                    self.scheme.delete()
                if self.password:
                    self.scheme = wifi.Scheme.for_cell(interface=IFACE,
                                                       name=self.cell.ssid,
                                                       cell=self.cell,
                                                       passkey=self.password.string)
                else:
                    self.scheme = wifi.Scheme.for_cell(interface=IFACE,
                                                       name=self.cell.ssid,
                                                       cell=self.cell)
                try:
                    self.scheme.save()
                except IOError:
                    gui.message_box(message="Not allowed to change network")
            try:
                self.scheme.activate()
            except wifi.exceptions.ConnectionError:
                gui.message_box(message="Incorrect Password")
            except IOError:
                gui.message_box(message="Not allowed to change network")
        elif label == "Forget":
            if self.scheme:
                self.scheme.delete()
        elif label == "Cancel":
            # do nothing
            pass
        super(CellSettings, self).close(label)

class UpdateBox(gui.Dialog):
    def __init__(self):
        super(UpdateBox, self).__init__((20, 20), (280, 160), "topleft")
        self.message = gui.StaticText((140, 80), (280, 60), "center",
                                      label="Updating OS...", parent=self)
        self.upgrade_thread = threading.Thread(target=self.upgrade)
        self.upgrade_thread.start()
        self.monitor = self.create_timer(self.upgrade_monitor, seconds=0.3)
        self.update(downwards=True)

    def upgrade(self):
        self.result = subprocess.call(['/usr/bin/tbupgrade', '--yes'])

    def upgrade_monitor(self):
        if not self.upgrade_thread.is_alive():
            self.monitor.stop()
            if self.result == 0:
                # probably should not get here...
                self.message.label = "Upgrade successful. Restarting..."
                self.create_timer(self.restart, seconds=1.0, repeating=False)
                self.update(downwards=True)
            elif self.result == 2:
                self.message.label = "Upgrade not needed"
                self.create_timer(lambda: self.close(None), seconds=1.0, repeating=False)
                self.update(downwards=True)
            else:
                self.message.label = "Error: " + str(self.result)
                self.create_timer(lambda: self.close(None), seconds=1.0, repeating=False)
                self.update(downwards=True)

    def restart(self):
        exit(0)

class Settings(gui.Dialog):
    # we're using a ScrollArea here in order to do the animation bit
    # but we need to alter it's functionality slightly
    def __init__(self, background_color=(0,0,0), callback=None, style=None):
        super(Settings, self).__init__((0, 0), (320, 206), "topleft",
                                       style=style, callback=callback, transition="slide_down")

        self.style.bg_color = background_color

        self.animate_timer.period = 1.0/30

        gui.StaticText((160, 23), (100, 20), parent=self.panel, label="Settings")
        # add widgets
        i = 0
        self.current_cell = tingbot.get_wifi_cell()
        if self.current_cell is not None:
            # fill in with basic details for now, but set scan running and we'll
            # update later
            self.cell_finder = threading.Thread(target=self.find_cells)
            self.cell_finder.start()
            self.version_checker = threading.Thread(target=self.check_versions)
            self.version_checker.start()
            self.thread_checker = self.create_timer(self.check_threads, seconds=0.3)
            if self.current_cell:
                cell_list = [self.current_cell]
            else:
                cell_list = ["Scanning..."]
            gui.StaticText((16, 59 + i*32), (120, 27), align="left",
                           parent=self.panel, label="Wi-Fi Network:", text_align="left")
            self.cell_dropdown = CellDropDown((313, 59 + i*32), (153, 27),
                                              align="right",
                                              parent=self.panel,
                                              values=cell_list)
            i += 1
        # show IP address
        ip_addr = tingbot.get_ip_address() or "No connection"
        gui.StaticText((16, 59 + i*32), (120, 27), align="left",
                       parent=self.panel, label="IP Address:", text_align="left")
        gui.StaticText((304, 59 + i*32), (153, 27), align="right",
                       parent=self.panel, label=ip_addr, text_align="right")
        i += 1
        # show tingbot version
        gui.StaticText((16, 59 + i*32), (120, 27), align="left",
                       parent=self.panel, label="Current version:", text_align="left")
        self.version_label = gui.StaticText((304, 59 + i*32), (120, 27), align="right",
                                            parent=self.panel, label="", text_align="right")
        i += 1
        # add update button but do not show it
        self.update_label = gui.StaticText((16, 59 + i*32), (120, 27), align="left",
                                           parent=self.panel,
                                           label="Update Available:",
                                           text_align="left")
        self.update_label.visible = False
        self.update_button = gui.Button((313, 59 + i*32), (120, 27), align="right",
                                        parent=self.panel, label="Update Now", callback=self.do_upgrade)
        self.update_button.visible = False
        self.update(downwards=True)

    def wifi_selected(self, name, cell):
        CellSettings(cell, self.style).run()

    def find_cells(self):
        try:
            self.cells = wifi.Cell.all(IFACE)
        except wifi.exceptions.InterfaceError:
            self.cells = []

    def check_versions(self):
        self.newer_version = True
        try:
            info = subprocess.check_output(['/usr/bin/tbupgrade', '--check-only'])
        except subprocess.CalledProcessError as e:
            info = e.output
            if e.returncode == 2:
                self.newer_version = False
        try:
            self.installed = re.search('Installed version:\s*(\d+.\d+.\d+)', info).group(1)
            self.latest = re.search('Latest version:\s*(\d+.\d+.\d+)', info).group(1)
        except AttributeError:
            print info
            self.installed = "Error"
            self.latest = "Error"

    def check_threads(self):
        if self.cell_finder and not self.cell_finder.is_alive():
            cell_list = [(x, x) for x in self.cells]
            self.cell_dropdown.values = cell_list
            self.cell_dropdown.callback = self.wifi_selected
            if cell_list:
                self.cell_dropdown.selected = cell_list[0]
            else:
                self.cell_dropdown.selected = ("No wifi signals", None)
            self.cell_finder = None
            self.update(downwards=True)
        if self.version_checker and not self.version_checker.is_alive():
            self.version_label.label = self.installed
            if self.newer_version:
                self.update_button.label = "Update to " + self.latest
                self.update_button.visible = True
                self.update_label.visible = True
            self.version_checker = None
            self.update(downwards=True)
        if self.version_checker is None and self.cell_finder is None:
            self.thread_checker.stop()

    def do_upgrade(self):
        UpdateBox().run()

    def animation_easing(self, number, towards):
        # TODO remove when added to tingbot-gui
        '''
        Returns the amount to change 'number' for a frame of animation. If animation should
        stop, return 0.
        '''
        change = int(towards - number) * 0.15

        # always round away from zero to prevent the animation getting stuck when fractional
        # changes are calculated
        if change > 0:
            return math.ceil(change)
        else:
            return math.floor(change)

    def animate(self):
        # TODO remove when added to tingbot-gui
        if self.transition=="slide_down":
            change = self.animation_easing(self.panel_pos[1], towards=0)
            self.panel_pos[1] += change
            self.bg_pos[1] += change
        elif self.transition=="slide_up":
            change = self.animation_easing(self.panel_pos[1] + self.panel.size[1], towards=240)
            self.panel_pos[1] += change
            self.bg_pos[1] += change
        elif self.transition=="slide_right":
            change = self.animation_easing(self.panel_pos[0], towards=0)
            self.panel_pos[0] += change
            self.bg_pos[0] += change
        elif self.transition=="slide_left":
            change = self.animation_easing(self.panel_pos[0] + self.panel.size[0], towards=320)
            self.panel_pos[0] += change
            self.bg_pos[0] += change
        if change==0:
            self.animate_timer.stop()

        self.update()

    def deanimate(self):
        # TODO remove when added to tingbot-gui
        if self.transition=="slide_down":
            change = self.animation_easing(self.bg_pos[1], towards=0)
            self.panel_pos[1] += change
            self.bg_pos[1] += change
        elif self.transition=="slide_up":
            change = self.animation_easing(self.bg_pos[1], towards=0)
            self.panel_pos[1] += change
            self.bg_pos[1] += change
        elif self.transition=="slide_right":
            change = self.animation_easing(self.bg_pos[0], towards=0)
            self.panel_pos[0] += change
            self.bg_pos[0] += change
        elif self.transition=="slide_left":
            change = self.animation_easing(self.bg_pos[0], towards=0)
            self.panel_pos[0] += change
            self.bg_pos[0] += change
        self.update()
        if change == 0:
            self.deanimate_timer.stop()
            self.close_final()

    def draw(self):
        # TODO remove when added to tingbot-gui
        if self.transition=="popup":
            return
        else:
            self.surface.blit(self.panel.surface,self.panel_pos)
            self.surface.blit(self.screen_copy,self.bg_pos)  
            tingbot.screen.needs_update = True
