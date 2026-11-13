import argparse
import os
from pathlib import Path
import uvicorn
from station.lora.radio import Radio
from station.lora.transport import SimulatedLink, SerialModem
from .receiver import Receiver, Listener
from .wifi import Wifi
from .web import create_app

def main():
    p = argparse.ArgumentParser(description='ACORN LoRa link (simulated transport) ground receiver')
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=8092)
    p.add_argument('--transport', choices=('simulated', 'serial'), default='simulated')
    p.add_argument('--serial-port', default='')
    p.add_argument('--udp-host', default='127.0.0.1')
    p.add_argument('--udp-port', type=int, default=9901)
    p.add_argument('--data', type=Path, default=Path('data'))
    p.add_argument('--station-url', default='http://127.0.0.1:8091')
    p.add_argument('--sf', type=int, default=10)
    p.add_argument('--bandwidth', type=int, default=125000)
    p.add_argument('--coding-rate', type=int, default=1)
    p.add_argument('--stale-after', type=float, default=660)
    p.add_argument('--lost-after', type=float, default=1200)
    a = p.parse_args()
    radio = Radio(a.sf, a.bandwidth, a.coding_rate)
    link = SimulatedLink(bind=(a.udp_host, a.udp_port)) if a.transport == 'simulated' else SerialModem(a.serial_port, sf=a.sf, bandwidth=a.bandwidth, coding_rate=a.coding_rate)
    receiver = Receiver(a.data, radio, a.stale_after, a.lost_after, transport_label=link.label)
    wifi = Wifi(a.station_url, os.environ.get('ACORN_STATION_SECRET'), a.data)
    uvicorn.run(create_app(receiver, wifi, Listener(receiver, link)), host=a.host, port=a.port)

if __name__ == '__main__':
    main()
