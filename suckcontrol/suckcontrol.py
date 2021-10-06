import sys
import logging
import webbrowser
from time import sleep
import PySimpleGUI as sg
from psgtray import SystemTray
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
sleep(7)  # Wait till all the hardware is loaded


def get_active_controls():
    # Get all the control sensors from config to disable slider
    controls = [control['sensor_controls'] for control in config.config['user'] if control['enabled']]
    controls = [value for values in controls for value in values]
    return controls


def set_default(index):
    for ident in config.config['user'][index]['sensor_controls']:
        config.sensors_control[ident].Control.SetDefault()


def open_url(url):
    b = webbrowser.get('windows-default')
    b.open(url)


devices = config.config['devices']
rules = [[]]
for rule in config.config['user']:
    title = f'{devices[rule["sensor_temp"]]} & {devices[rule["sensor_controls"][0]]}'
    points = rule['points']
    enabled = rule['enabled']
    key = f'{rule["sensor_temp"]}_{rule["sensor_controls"][0]}'
    tooltip = ''
    tooltip += '\n'.join([f'{devices[control]}' for control in rule["sensor_controls"]])
    start_point = (points[0][0] - 5, points[0][1] - 5)
    end_point = (points[-1][0] + 5, points[-1][1] + 5)
    rules[-1].append(
        sg.Frame(title, [
            [sg.Graph(canvas_size=(200, 200), graph_bottom_left=start_point, graph_top_right=end_point, background_color='grey', key=f'graph_{key}')],
            [sg.Button('Edit', key=f'btn_{key}_Edit'),
             sg.Button('Delete', key=f'btn_{key}_Delete'),
             sg.Checkbox('Enabled', default=enabled, key=f'chk_{key}_enabled', enable_events=True)]
        ],
                 key=key,
                 tooltip=tooltip)
    )

    # New row
    if len(rules[-1]) == 5:
        rules.append([])

controls = get_active_controls()
sensor_objects = {}
sensor_controllers = [[]]
sensor_fans = [[]]
sensor_temps = [[]]
for ident, sensor in config.sensors_all.items():
    title = sensor.Name
    value = int(sensor.Value)
    if sensor.SensorType == 9:
        if ident in controls:
            disabled = True
            color = 'grey'
        else:
            disabled = False
            color = sg.theme_slider_color()
        sensor_objects[ident] = sg.Slider(range=(0, 100), default_value=value, orientation='h', size=(20, 15),
                                          key=f'sld_{ident}', enable_events=True, disabled=disabled, trough_color=color)
        sensor_controllers.append(
            [sg.Frame(title, [  # [sg.Text(f'{value}%', size=(14, 2))],
                [sensor_objects[ident], sg.Button('Reset', key=f'btn_{ident}_Reset', disabled=disabled)]])]
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

menu = [[name, ['GitHub::mn_github', '!Reload Hardware', 'Exit', ]],
        ['How to', [f'{name}::mn_ht_{name}', 'Airflow::mn_ht_airflow']], ]

layout = [[sg.Menu(menu), sg.Frame('Rules', rules)],
          [sg.Column([[sg.Frame('Controllers', sensor_controllers)]]),
           sg.Column([[sg.Frame('Fans', sensor_fans)]]),
           sg.Column([[sg.Frame('Temperatures', sensor_temps)]])],
          [sg.Button('Add Rule', key='btn_AddRule')]]

window = sg.Window(name, layout, finalize=True, alpha_channel=0, enable_close_attempted_event=True, icon='icon.ico',
                   location=sg.user_settings_get_entry('-location-', (None, None)))
window.hide()
window_hidden = True

tray_menu = ['', ['Open', 'Exit']]
tray = SystemTray(tray_menu, single_click_events=True, window=window, tooltip=name, icon=r'icon.ico')
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
            sg.user_settings_set_entry('-location-', window.current_location())
            window.hide()
            window_hidden = True
    elif event == sg.WIN_CLOSE_ATTEMPTED_EVENT:
        sg.user_settings_set_entry('-location-', window.current_location())
        window.hide()
        window_hidden = True
    elif event in (sg.WIN_CLOSED, 'Exit'):  # Triggered via tray and menu
        break

    # Proceed only if window is shown
    if window_hidden:
        continue

    event_data = event.split('::')[-1].split('_')
    # Check for button clicks
    if event_data[0] == 'btn':
        if event_data[-1] == 'AddRule':
            # TODO: https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Layout_Extend.py
            pass
        elif event_data[-1] == 'Delete':
            first_controller = event_data[2]
            for i, rule in enumerate(config.config['user']):
                if rule['sensor_controls'][0] == first_controller:
                    set_default(i)
                    config.config['user'].pop(i)
                    config.save()
                    rule_element = window.find_element(f'{event_data[1]}_{event_data[2]}')
                    rule_element.update(visible=False)
                    for ident in rule['sensor_controls']:
                        sensor_objects[ident].update(disabled=False)
                        sensor_objects[ident].Widget.config(troughcolor=sg.theme_slider_color())
                        window.find_element(f'btn_{ident}_Reset').update(disabled=False)
                    break
        elif event_data[-1] == 'Edit':
            pass
        elif event_data[-1] == 'Reset':
            config.sensors_control[event_data[1]].Control.SetDefault()
    elif event_data[0] == 'sld':
        if 'control' in event_data[1]:
            config.sensors_control[event_data[1]].Control.SetSoftware(values[event])
    elif event_data[0] == 'chk':
        if event_data[-1] == 'enabled':
            first_controller = event_data[2]
            for i, rule in enumerate(config.config['user']):
                if rule['sensor_controls'][0] == first_controller:
                    enabled = not config.config['user'][i]['enabled']
                    config.config['user'][i]['enabled'] = enabled
                    config.save()
                    set_default(i)
                    if enabled:
                        color = 'grey'
                    else:
                        color = sg.theme_slider_color()
                    for ident in rule['sensor_controls']:
                        sensor_objects[ident].update(disabled=enabled)
                        sensor_objects[ident].Widget.config(troughcolor=color)
                        window.find_element(f'btn_{ident}_Reset').update(disabled=enabled)
    # Check for menu clicks
    elif event_data[0] == 'mn':
        if event_data[1] == 'github':
            open_url('https://github.com/Nama/SuckControl/')
        elif event_data[1] == 'ht':
            if event_data[2] == name:
                open_url('https://github.com/Nama/SuckControl/wiki/How-to-use')
            elif event_data[2] == 'airflow':
                open_url('https://github.com/Nama/SuckControl/wiki/How-to-airflow')

    # Update values in window
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

    # Update graphs of rules
    for rule in config.config['user']:
        points = rule['points']
        key = f'{rule["sensor_temp"]}_{rule["sensor_controls"][0]}'
        graph = window.find_element(f'graph_{key}')
        graph.erase()
        size = 1
        relative_size = (1 / 100) * max(points[-1])

        # Draw axis
        canvas_size = graph.CanvasSize
        start_point = (points[0][0] - 5, points[0][1] - 5)
        end_point = (points[-1][0] + 5, points[-1][1] + 5)
        #graph.DrawLine((-5, start_point[1] + 3), (canvas_size[0], start_point[1] + 3))
        #graph.DrawLine((start_point[0] + 3, -5), (start_point[0] + 3, canvas_size[0]))

        for i, point in enumerate(points):
            graph.draw_point(point, color='red', size=relative_size)
            graph.draw_text(point, point)
            if point != points[-1]:
                graph.draw_line(point, points[i+1], color='red')
        # Line should be extended to the borders of the graphs
        graph.draw_line((-5, points[0][1]), points[0], color='red')
        graph.draw_line(points[-1], (100, points[-1][1]), color='red')

        ident_control = rule['sensor_controls'][0]
        speed = int(config.sensors_control[ident_control].Value)
        ident_temp = rule['sensor_temp']
        temp = int(config.sensors_temp[ident_temp].Value)
        current_point = [temp, speed]
        if temp < start_point[0] or speed < start_point[1]:
            current_point_location = [start_point[0], speed]
        else:
            current_point_location = current_point
        graph.draw_point(current_point_location, color='green', size=relative_size + 0.5)
        current_point_text = [current_point_location[0] + 4, current_point_location[1] + 4]
        graph.draw_text(current_point, current_point_text, color='green')

config.terminate = True
config.stop()
sleep(1)  # Wait for clean exit
tray.close()
window.close()
