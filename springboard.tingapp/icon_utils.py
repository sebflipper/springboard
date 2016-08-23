import os
import tingbot


def iconise(fname):
    return os.path.join(os.path.dirname(__file__), 'icons', 'Icon_' + fname)


def get_network_icon_name(cell):
    if cell and cell.ssid:
        if hasattr(cell, 'link_quality'):
            quality = min(99, max(cell.link_quality * 100 / 70, 0))
        else:
            quality = min(99, max((110+cell.signal) * 100 / 70, 0))
            
        return 'WiFi-%d.png' % (int(quality / 20) + 2)
    elif tingbot.get_ip_address():
        # has network connection that's not wifi, must be ethernet
        return 'Ethernet-1.png'
    else:
        # has no network connection
        return 'WiFi-1.png'
