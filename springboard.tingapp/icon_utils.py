import os

def iconise(fname):
    return os.path.join(os.path.dirname(__file__),'icons',fname)

def get_network_icon_name(cell):
    if cell and cell.ssid:
        if hasattr(cell,'link_quality'):
            quality = min(100, max(cell.link_quality * 100 / 70, 0))
        else:
            quality = min(100, max((110+cell.signal) * 100 / 70, 0))
    else:
        if get_ip_address():
            quality = -1 # wired network
        else:
            quality = 0 # no connection
    if quality == -1:
        return 'wired.png'
    else:
        return 'wifi-%03d.png' % (int(quality/20)*20)
