import functools
import time
import json

import evil
import tingbot

NETWORK_INFO = '/boot/networks.json'
TIMEOUT = 10


@functools.total_ordering
class Cell(object):
    def __init__(self, ssid):
        self.ssid = ssid
        self.present = False
        self.known = False
        self.connected = False
        self.signal = -1000
        self.type = None
        self.passphrase = None

    def load_from_evil(self,evil_cell):
        self.present = True
        self.signal = int(evil_cell['sig'])
        if 'WPA2' in evil_cell['flag']:
            self.type = "WPA2"
        elif 'WPA' in evil_cell['flag']:
            self.type = "WPA"
        elif 'WEP' in evil_cell['flag']:
            self.type = "WEP"
        else:
            self.type = "OPEN"
        

    def load_from_json(self, cell):
        self.known = True
        self.passphrase = cell['passphrase']
        
    def _key(self):
        return (self.connected,self.present,self.known,self.signal,self.ssid)
        
    def __lt__(self,other):
        return self._key() > other._key()

    def __eq__(self, other):
        return self._key() == other._key()
        
    def __repr__(self):
        return "[%s]: %s %s Signal: %d" % (self.ssid, 
                                           ("Absent ","Present ")[self.present], 
                                           ("Unknown","Known  ")[self.known],
                                           self.signal)

def find_networks(iface):
    evil_cells = evil.get_networks(iface) or []
    try:
        with open(NETWORK_INFO,'r') as f:
            json_cells = json.load(f)
    except (IOError, TypeError, ValueError):
        json_cells = []
    networks = {}
    for x in evil_cells:
        ssid = x['ssid']
        networks[ssid] = Cell(ssid)
        networks[ssid].load_from_evil(x)
    for x in json_cells:
        ssid = x['ssid']
        if ssid not in networks:
            networks[ssid] = Cell(ssid)
        networks[ssid].load_from_json(x)
    current_cell = tingbot.hardware.get_wifi_cell()
    if current_cell and current_cell.ssid in networks:
        networks[current_cell.ssid].connected = True
    return sorted(networks.values())
    
def save_cell(cell):
    with open(NETWORK_INFO, 'r') as f:
        json_cells = json.load(f)
    json_cells = [x for x in json_cells if x['ssid'] != cell.ssid]
    if cell.passphrase:
        json_cells += [{'ssid': cell.ssid, 'passphrase': cell.passphrase}]
    with open(NETWORK_INFO, 'w') as f:
        json.dump(json_cells,f)
        
def delete_cell(cell):
    with open(NETWORK_INFO, 'r') as f:
        json_cells = json.load(f)
    json_cells = [x for x in json_cells if x['ssid'] != cell.ssid]
    with open(NETWORK_INFO, 'w') as f:
        json.dump(json_cells,f)

def connect(iface, cell):
    evil.connect_to_network(iface, cell.ssid, cell.type, cell.passphrase)
    for i in range(TIMEOUT):
	if evil.is_associated(iface):
            break
        time.sleep(1)
    evil.do_dhcp(iface)
    for i in range(TIMEOUT):
        if evil.has_ip(iface):
            break
        time.sleep(1)


