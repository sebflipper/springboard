import functools
import time
import json
import logging
import subprocess

import evil
import tingbot

NETWORK_INFO = '/boot/networks.json'
TIMEOUT = 30


@functools.total_ordering
class Cell(object):
    def __init__(self, ssid):
        self.ssid = ssid
        self.present = False
        self.connected = False
        self.signal = -1000
        self.type = None

    def load_from_evil(self, evil_cell):
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
        return (self.connected,self.present,self.signal,self.ssid)
        
    def __lt__(self,other):
        return self._key() > other._key()

    def __eq__(self, other):
        return self._key() == other._key()
        
    def __repr__(self):
        return "[%s]: %s Signal: %d" % (self.ssid, 
                                        ("Absent ","Present ")[self.present], 
                                        self.signal)

class WifiError(Exception):
    pass

def _networks_json():
    try:
        with open(NETWORK_INFO, 'r') as f:
            return json.load(f)
    except (IOError, TypeError, ValueError) as e:
        logging.exception(e)
        return []

def _set_networks_json(networks):
    with open(NETWORK_INFO, 'w') as f:
        json.dump(networks, f)
    
def _save_cell(ssid, passphrase):
    json_cells = _networks_json()

    json_cells = [x for x in json_cells if x['ssid'] != ssid]

    json_cells.insert(0, {'ssid': ssid, 'passphrase': passphrase})

    _set_networks_json(json_cells)

def _delete_cell(ssid):
    json_cells = _networks_json()

    json_cells = [x for x in json_cells if x['ssid'] != ssid]

    _set_networks_json(json_cells)

def find_networks(iface):
    evil_cells = evil.get_networks(iface) or []

    networks = {}

    for x in evil_cells:
        ssid = x['ssid']
        networks[ssid] = Cell(ssid)
        networks[ssid].load_from_evil(x)

    current_cell = tingbot.hardware.get_wifi_cell()
    if current_cell and current_cell.ssid in networks:
        networks[current_cell.ssid].connected = True

    return sorted(networks.values())

def stored_passphrase(ssid):
    for network_dict in _networks_json():
        if network_dict['ssid'] == ssid:
            return network_dict['passphrase']

    return None

def connect(iface, cell, passphrase):
    try:
        evil.connect_to_network(iface, cell.ssid, cell.type, passphrase)

        for i in range(TIMEOUT):
            if evil.is_associated(iface):
                break
            if i == TIMEOUT - 1:
                raise WifiError('Wifi association timeout')
            time.sleep(1)

        evil.do_dhcp(iface)

        for i in range(TIMEOUT):
            if evil.has_ip(iface):
                break
            if i == TIMEOUT - 1:
                raise WifiError('DHCP timeout')
            time.sleep(1)

        # connection was successful, so let's save that to /boot/networks.json
        _save_cell(cell.ssid, passphrase)
        # update the wpa config file from /boot/networks.json
        subprocess.check_call(['/usr/bin/tbwifisetup'])
    finally:
        # if connection was unsuccessful, this will reload previous configuration
        subprocess.check_call(['/sbin/wpa_cli', 'reconfigure'])

def forget_cell(ssid):
    _delete_cell(ssid)
