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
    
class MemoryWidget(gui.Widget):
    def __init__(self, xy, size, parent, surface, surface_area):
        super(MemoryWidget,self).__init__(xy, size, "topleft", parent)
        self.memory_surface = pygame.Surface(surface_area.size,0,surface)
        self.memory_surface.blit(surface,(0,0),surface_area)
        
    def draw(self):
        self.surface.blit(self.memory_surface,(0,0))

class Settings(gui.ScrollArea):
    #we're using a ScrollArea here in order to do the animation bit
    #but we need to alter it's functionality slightly
    def __init__(self,style=None):
        super(Settings,self).__init__((0,0), (320,240), "topleft", canvas_size=(320,440),style=style)
        self.viewport.position=[0,200]
        tingbot.every(seconds=0.02)(self.animate)
        memory = MemoryWidget((0,200),(320,240),self.scrolled_area,tingbot.screen.surface,pygame.Rect((0,0),(320,240)))
        style14 = self.style.copy(statictext_font_size=14, button_text_font_size=14)
        gui.StaticText((160,23), (100,20), parent=self.scrolled_area, style=style14, label="Settings")
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
                               parent=self.scrolled_area, label="Wi-Fi Network:", text_align="left")
                gui.DropDown((313,59+i*32),(153,27),align="right", style=style14,
                             parent=self.scrolled_area, values = cell_list,callback = self.wifi_selected)
                i += 1
        #show IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        s.connect(("8.8.8.8",80))
        ip_addr = s.getsockname()[0]
        s.close()
        gui.StaticText((16,59+i*32), (120,27), align="left", style=style14, 
                       parent=self.scrolled_area, label="IP Address:", text_align="left")
        gui.StaticText((304,59+i*32), (153,27), align="right", style=style14, 
                       parent=self.scrolled_area, label=ip_addr, text_align="right")
        i += 1
        #show tingbot version
        gui.StaticText((16,59+i*32), (120,27), align="left", style=style14,
                       parent=self.scrolled_area, label="Tingbot OS:", text_align="left")
        gui.StaticText((304,59+i*32), (120,27), align="right", style=style14,
                       parent=self.scrolled_area, label=tingbot.__version__, text_align="right")
        i +=1
        #show update button
        if can_update_os():
            gui.StaticText((16,59+i*32),(120,27), align="left", style=style14,
                           parent=self.scrolled_area, label="Update Available:", text_align="left")
            gui.Button((313,59+i*32),(120,27), align="right", style=style14,
                       parent=self.scrolled_area, label="Update Now", callback=update_os)
                           
        
       
    def resize_canvas(self,canvas_size):
        #disable slider creation
        pass
        
    def on_touch(self, xy, action):
        #disable most of the flick capability etc by bypassing viewport's on_touch
        if xy[1]>200:
            self.visible=False
        self.viewport.panel.on_touch(tingbot.graphics._xy_add(xy, self.viewport.position), action)
        
    def animate(self):
        #move self down a bit over 1 second, then stop
        self.viewport.position[1] -= 10
        if self.viewport.position[1] <= 0:
            tingbot.once()(self.end_animation) #queue up an end_animate - can't be called directly from animate
            self.viewport.position[1] = 0
        self.update()
        self.update(downwards=True)
        
    def end_animation(self):
        tingbot.main_run_loop.remove_timer(self.animate)

    def wifi_selected(self,name,cell):
        print cell.ssid
