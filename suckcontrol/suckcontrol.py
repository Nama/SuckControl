# https://github.com/PySimpleGUI/PySimpleGUI/issues/3881
# https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Layout_Extend.py

import os
import sys
import logging
from time import sleep
import PySimpleGUI as sg
from psgtray import SystemTray
from pathlib import Path
from configcontrol import Config
from daemon import start_daemons

try:
    loglevel = sys.argv[1]
except IndexError:
    loglevel = 'INFO'
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)

logger = logging.getLogger('suckcontrol')
logger.setLevel(numeric_level)
logfile = logging.FileHandler('suckcontrol.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s %(lineno)d: %(message)s')
logfile.setFormatter(formatter)
logger.addHandler(logfile)

config = Config()
config_moved = config.load()
start_daemons(config)
name = 'SuckControl'
sg.theme('DarkGrey12')
sleep(5)

devices = config.config['devices']
rules = [[]]
for rule in config.config['user']:
    title = f'{devices[rule["sensor_temp"]]} & {devices[rule["sensor_controls"][0]]}'
    points = rule['points']
    key = f'{rule["sensor_temp"]}{rule["sensor_controls"][0]}'
    rules[-1].append(
        sg.Frame(title, [
            [sg.Text(points)],
            [sg.Button('Edit', key=f'{key}Edit'),
            sg.Button('Delete', key=f'{key}Delete')]
        ],
                 key=key)
    )

    # New row
    if len(rules[-1]) == 5:
        rules.append([])

sensor_objects = {}
sensor_controllers = [[]]
sensor_fans = [[]]
sensor_temps = [[]]
for ident, sensor in config.sensors_all.items():
    title = sensor.Name
    value = int(sensor.Value)
    if sensor.SensorType == 9:
        sensor_objects[ident] = sg.Slider(range=(0, 100), default_value=value, orientation='h', size=(20, 15), key=ident, enable_events=True)
        sensor_controllers.append(
            [sg.Frame(title, [#[sg.Text(f'{value}%', size=(14, 2))],
                              [sensor_objects[ident]]])]
        )
    elif sensor.SensorType == 7:
        sensor_objects[ident] = sg.Text(f'{value} RPM', size=(14, 2), key=ident)
        sensor_fans.append(
            [sg.Frame(title, [[sensor_objects[ident]]])]
        )
    elif sensor.SensorType == 4:
        sensor_objects[ident] = sg.Text(f'{value} °C', size=(14, 2), key=ident)
        sensor_temps.append(
            [sg.Frame(title, [[sensor_objects[ident]]])]
        )

layout = [[sg.Frame('Rules', rules)],
          [sg.Column([[sg.Frame('Controllers', sensor_controllers)]]),
           sg.Column([[sg.Frame('Fans', sensor_fans)]]),
           sg.Column([[sg.Frame('Temperatures', sensor_temps)]])],
          [sg.Button('Add Rule', key='btn_AddRule')]]

window = sg.Window(name, layout, finalize=True, alpha_channel=0, enable_close_attempted_event=True)
window.hide()
window_hidden = True

menu = ['', ['Open', 'Exit']]
tray = SystemTray(menu, single_click_events=True, window=window, tooltip=name, icon=r'suckcontrol.png')
while True:
    event, values = window.read(timeout=1500)
    if event == tray.key:
        event = values[event]

    # Tray actions
    if event in ('Open', sg.EVENT_SYSTEM_TRAY_ICON_ACTIVATED):  # Single click
        if window_hidden:
            window.set_alpha(1)
            window.un_hide()
            window_hidden = False
        elif not window_hidden:
            window.hide()
            window_hidden = True
    elif event == sg.WIN_CLOSE_ATTEMPTED_EVENT:
        window.hide()
        window_hidden = True
    elif event in (sg.WIN_CLOSED, 'Exit'):
        break

    # Only if window is shown
    if window_hidden:
        continue
    if event == 'btn_AddRule':
        sensor_objects['Yorp'].update('9999')

    for ident, sensor in config.sensors_all.items():
        # Prevent the event loop setting the sliders while the user moves them
        if sensor.SensorType == 9 and 'control' not in event:
            value = int(sensor.Value)
        elif sensor.SensorType == 7:
            value = str(f'{int(sensor.Value)} RPM')
        elif sensor.SensorType == 4:
            value = str(f'{int(sensor.Value)} °C')
        sensor_objects[ident].update(value)
    window.refresh()

config.terminate = True
config.stop()
tray.close()
window.close()
