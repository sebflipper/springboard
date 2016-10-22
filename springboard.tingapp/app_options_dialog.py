import tingbot, os, errno, shutil
import tingbot_gui as gui

def symlink_force(target, link_name):
    try:
        os.symlink(target, link_name)
    except OSError, e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(target, link_name)
        else:
            raise e

def style(**kwargs):
    style = gui.get_default_style().copy()
    for key, value in kwargs.iteritems():
        setattr(style, key, value)
    return style

def startup_app():
    try:
        return os.readlink('/apps/startup')
    except Exception as e:
        print e
    
def set_startup_app(app_path):
    if app_path:
        symlink_force(app_path, '/apps/startup')
    else:
        symlink_force('/apps/home', '/apps/startup')

class AppOptionsDialog(gui.Dialog):
    def __init__(self, app):
        super(AppOptionsDialog, self).__init__(
            size=(260, 160),
            align="center")
        
        self.app = app
        self.style.bg_color = app.background_color

        self.app_name_label = gui.StaticText(
            xy=(160, 62),
            size=(180, 30),
            align="center",
            label=app.name,
            parent=self)
        
        self.close_button = gui.Button(
            xy=(290, 40),
            size=(40, 40),
            align="topright",
            parent=self,
            label="image:whitecross.png",
            style=style(
                button_inverting=False,
                button_color=self.style.bg_color,
                button_rounding=False,),
            callback=self.close)
        
        self.set_startup_app_button = gui.ToggleButton(
            xy=(160, 108),
            size=(220, 40),
            align="center",
            label='Launch on startup',
            parent=self,
            style=style(
                button_rounding=False),
            callback=self.toggle_startup_app)
        
        self.delete_button = gui.Button(
            xy=(160, 160),
            size=(220, 40),
            align="center",
            label='Delete',
            parent=self,
            style=style(
                button_color=(255, 70, 70),
                button_rounding=False),
            callback=self.delete_button_pressed)
        
        self.refresh()
    
    def refresh(self):
        is_startup_app = (startup_app() == self.app.path)
        
        self.set_startup_app_button.pressed = is_startup_app
        self.set_startup_app_button.update()

    def toggle_startup_app(self, value):
        if value:
            set_startup_app(self.app.path)
        else:
            set_startup_app(None)
        self.refresh()

    def delete_button_pressed(self):
        message_box = gui.MessageBox(
            size=(260, 160),
            style=style(
                messagebox_button_size=(110, 35)),
            message='Delete the app "%s"?' % self.app.name,
            buttons=['Cancel', 'Delete'])
            
        button = message_box.run()
        
        if button == 'Delete':
            shutil.rmtree(self.app.path)
            self.close('deleted')
