import socket
import threading
import subprocess
import re
import math

import pygame
import tingbot
import tingbot_gui as gui

from icon_utils import get_network_icon_name, iconise
import wifi
import evil

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
        if (cell.type in ('WPA2','WPA','WEP')):
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
        buttons = []
        stored_passphrase = wifi.stored_passphrase(cell.ssid)

        if cell.present:
            buttons += ['Connect']
        if stored_passphrase is not None:
            buttons += ['Forget']
        buttons += ['Cancel']    
        
        super(CellSettings, self).__init__((20, 20), (280, 160), "topleft", style=style,
                                           buttons=buttons)
        gui.StaticText((140, 0), (100, 30), "top", parent=self.panel, label=cell.ssid)
        self.cell = cell

        if cell.type in ("WPA","WPA2","WEP"):
            pwd = stored_passphrase or ""
            gui.StaticText((10, 55), (90, 30), "left", label="Password:",
                           style=style, parent=self.panel)
            self.password = gui.PasswordEntry((270, 55), (160, 30), "right", parent=self.panel,
                                              label="Password", string=pwd)
        else:
            self.password = None

    def close(self, label):
        if label == "Connect": # self.present must be true
            passphrase = ""
            if self.password:
                passphrase = self.password.string
                
            try:
                wifi.connect(IFACE, self.cell, passphrase)
            except (evil.EvilError, wifi.WifiError) as e:
                print e
                gui.message_box(message="Failed: %s" % e)
        elif label == "Forget":
            wifi.forget_cell(self.cell)
        elif label == "Cancel":
            # do nothing
            pass
        super(CellSettings, self).close(label)


class UpdateBox(gui.Dialog):
    def __init__(self):
        super(UpdateBox, self).__init__((20, 20), (280, 160), "topleft")

        self.message = gui.StaticText((160, 70), (240, 30), "center",
                                      label="Updating OS...", parent=self)
        self.log_header_text = gui.StaticText((160, 100), (240, 30), "center",
                                              label="", parent=self)
        self.log_text = gui.StaticText((160, 130), (240, 30), "center",
                                       label="", parent=self)

        self.latest_log_header = ''
        self.latest_log = ''
        self.result = None
        self.upgrade_thread = threading.Thread(target=self.upgrade)
        self.upgrade_thread.start()
        self.monitor = self.create_timer(self.upgrade_monitor, seconds=0.1)
        self.update(downwards=True)

    def upgrade(self):
        upgrade_process = subprocess.Popen(
            ['/usr/bin/tbupgrade', '--yes'],
            stdout=subprocess.PIPE,
            universal_newlines=True)

        log_header_re = re.compile(r'^tbupgrade: ([A-Za-z0-9].*)$')
        log_re = re.compile(r'^(tbupgrade: |  )?([A-Za-z0-9].*)$')
        
        for line in iter(upgrade_process.stdout.readline, ''):
            log_header_match = log_header_re.match(line)
            if log_header_match:
                self.latest_log_header = log_header_match.group(1)
                self.latest_log = ''
            else:
                log_match = log_re.match(line)
                if log_match:
                    self.latest_log = log_match.group(2)

        self.result = upgrade_process.wait()

    def upgrade_monitor(self):
        if self.upgrade_thread.is_alive():
            self.log_header_text.label = self.latest_log_header
            self.log_text.label = self.latest_log
            
            self.update(downwards=True)
        else:
            self.log_header_text.label = ''
            self.log_text.label = ''
            self.monitor.stop()
            
            if self.result == 0:
                self.message.label = "Upgrade successful. Restarting..."
                self.create_timer(self.restart, seconds=4.0, repeating=False)
            elif self.result == 2:
                self.message.label = "You're up to date!"
                self.create_timer(lambda: self.close(None), seconds=4.0, repeating=False)
            else:
                self.message.label = "Error: " + str(self.result)
                self.create_timer(lambda: self.close(None), seconds=4.0, repeating=False)
            
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
        self.cells = []

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
                cell_list = [self.current_cell.ssid]
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
        gui.StaticText((16, 59 + i*32), (120, 27), align="left",
                       parent=self.panel, label="IP Address:", text_align="left")
        self.ip_label = gui.StaticText((304, 59 + i*32), (153, 27), align="right",
                                       parent=self.panel, label="", text_align="right")
        self.show_ip_address()
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
        
    def show_ip_address(self):
        self.ip_label.label = tingbot.get_ip_address() or "No connection"
        self.ip_label.update()

    def wifi_selected(self, name, cell):
        if cell:
            try:
                CellSettings(cell, self.style).run()
                self.find_cells()
            except evil.EvilError as e:
                gui.msgbox(str(e))
            self.show_ip_address()
            self.update_cell_dropdown()

    def find_cells(self):
        self.cells = wifi.find_networks(IFACE)

    def check_versions(self):
        self.newer_version = True
        self.installed = "Error"
        self.latest = "Error"
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
            
    def update_cell_dropdown(self):
            cell_list = [(x, x) for x in self.cells]
            if cell_list:
                if not any(x.connected for x in self.cells):
                    cell_list = [("Select network", None)] + cell_list
            else:
                cell_list = [("No wifi signals", None)]
            self.cell_dropdown.values = cell_list
            self.cell_dropdown.callback = self.wifi_selected
            self.cell_dropdown.selected = cell_list[0]
            self.cell_dropdown.update(downwards=True)

    def check_threads(self):
        if self.cell_finder and not self.cell_finder.is_alive():
            self.update_cell_dropdown()
            self.cell_finder = None
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
