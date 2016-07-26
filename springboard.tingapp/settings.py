import socket

import wifi
import pygame
import tingbot
import tingbot_gui as gui

IFACE = 'wlan0'

def get_os_version():
    return tingbot.__version__
    
def can_update_os():
    return True
    
def update_os():
    ###FIXME###
    print "updating OS"
    
class CellSettings(gui.MessageBox):
    def __init__(self, cell, style=None):
        super(CellSettings, self).__init__((20,20), (280,160), "topleft", style=style,
                                           buttons=['Connect','Forget','Cancel'])
        gui.StaticText((140,0),(100,30),"top",parent=self.panel, label=cell.ssid)
        self.cell = cell
        self.scheme = wifi.Scheme.find(IFACE,cell.ssid)
        if cell.encrypted:
            if self.scheme:
                pwd = "        "
            else:
                pwd = ""
            gui.StaticText((10,55), (90,30), "left", label="Password:",
                           style=style, parent=self.panel)
            self.password = gui.PasswordEntry((270,55), (160,30), "right", parent=self.panel,
                                              label="Password", string=pwd)
        else:
            self.password = None
           

    def close(self,label):
        if label == "Connect":
            if (self.scheme is None) or (self.password and self.password.string != "        "):
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
        super(CellSettings,self).close(label)        
    
class Settings(gui.Dialog):
    #we're using a ScrollArea here in order to do the animation bit
    #but we need to alter it's functionality slightly
    def __init__(self, callback = None, style=None):
        super(Settings,self).__init__((0,0), (320,200), "topleft",
                                      style=style, callback=callback, transition="slide_down")
        style14 = self.style.copy(statictext_font_size=14, button_text_font_size=14)
        gui.StaticText((160,23), (100,20), parent=self.panel, style=style14, label="Settings")
        #add widgets
        i = 0
        #add wifi list if dongle attached
        #need to make this auto-update every 30s or so...
        if 1:
            try:
                cells = wifi.Cell.all(IFACE)
            except wifi.exceptions.InterfaceError:
                #no dongle
                pass
            else:
                cell_list = [(x.ssid,x) for x in cells]
                gui.StaticText((16,59+i*32), (120,27), align="left", style=style14,
                               parent=self.panel, label="Wi-Fi Network:", text_align="left")
                dd = gui.DropDown((313,59+i*32),(153,27),align="right", style=style14,
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
        CellSettings(cell,self.style).run()
