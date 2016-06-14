import socket

import wifi
import pygame
import tingbot
import tingbot_gui as gui

def print_timers():
    print [x.action for x in tingbot.main_run_loop.timers]
    
def get_os_version():
    return tingbot.__version__
    
def can_update_os():
    return True
    
def update_os():
    ###FIXME###
    print "updating OS"
    
class Settings(gui.ModalWindow):
    #we're using a ScrollArea here in order to do the animation bit
    #but we need to alter it's functionality slightly
    def __init__(self, callback = None, style=None):
        super(Settings,self).__init__((0,0), (320,200), "topleft",
                                      style=style, callback=callback, transition="slide_down")
        print "settings start"                              
        style14 = self.style.copy(statictext_font_size=14, button_text_font_size=14)
        gui.StaticText((160,23), (100,20), parent=self.panel, style=style14, label="Settings")
        #add widgets
        i = 0
        #add wifi list if dongle attached
        #need to make this auto-update every 30s or so...
        if 0:
            try:
                cells = wifi.Cell.all('wlan0')
            except wifi.exceptions.InterfaceError:
                #no dongle
                pass
            else:
                cell_list = [(x.ssid,x) for x in cells]
                gui.StaticText((16,59+i*32), (120,27), align="left", style=style14,
                               parent=self.panel, label="Wi-Fi Network:", text_align="left")
                gui.DropDown((313,59+i*32),(153,27),align="right", style=style14,
                             parent=self.panel, values = cell_list,callback = self.wifi_selected)
                i += 1
        #show IP address
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
            s.connect(("8.8.8.8",80))
            ip_addr = s.getsockname()[0]
        except IOError:
            ip_addr = "No connection"
        finally:
            s.close()
        gui.StaticText((16,59+i*32), (120,27), align="left", style=style14, 
                       parent=self.panel, label="IP Address:", text_align="left")
        gui.StaticText((304,59+i*32), (153,27), align="right", style=style14, 
                       parent=self.panel, label=ip_addr, text_align="right")
        i += 1
        #show tingbot version
        gui.StaticText((16,59+i*32), (120,27), align="left", style=style14,
                       parent=self.panel, label="Tingbot OS:", text_align="left")
        gui.StaticText((304,59+i*32), (120,27), align="right", style=style14,
                       parent=self.panel, label=tingbot.__version__, text_align="right")
        i +=1
        #show update button
        if can_update_os():
            gui.StaticText((16,59+i*32),(120,27), align="left", style=style14,
                           parent=self.panel, label="Update Available:", text_align="left")
            gui.Button((313,59+i*32),(120,27), align="right", style=style14,
                       parent=self.panel, label="Update Now", callback=update_os)
        self.update(downwards=True)
        
    def wifi_selected(self,name,cell):
        print cell.ssid
