import os
import sys
import webbrowser
import logging
import notify
from pathlib import Path
from waitress import serve
from configcontrol import Config
from daemon import start_daemons
from infi.systray import SysTrayIcon
from flask import Flask, render_template, request, redirect, url_for

try:
    loglevel = sys.argv[1]
except IndexError:
    loglevel = 'ERROR'
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

folder = Path(config.root_path, 'html')
app = Flask(__name__, static_folder=str(folder), template_folder=str(folder))
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1


@app.route('/')
def index():
    # Get all the control sensors from config to disable slider
    controls = [control['sensor_controls'] for control in config.config['user'] if control['enabled']]
    controls = [value for values in controls for value in values]
    return render_template('index.html', rules=config.config['user'], config=config.config['devices'], main=config.config['main'], sensors_list=(config.sensors_control, config.sensors_fan, config.sensors_temp), controls=controls)


@app.route('/add_rule')
def add_rule():
    # Get all the control sensors from config to hide them
    controls = [control['sensor_controls'] for control in config.config['user']]
    controls = [value for values in controls for value in values]
    return render_template('add_rule.html', sensors_all=config.sensors_all, controls=controls, main=config.config['main'])


@app.route('/save_rule', methods=['POST'])
def save_rule():
    data = request.json
    tempsensor = data['temp']
    controlsensors = data['controls']
    tempvalues = data['tempvalues']
    controlvalues = data['controlvalues']
    values = zip(tempvalues, controlvalues)
    config.config['user'].append({
        'enabled': True,
        'sensor_temp': tempsensor,
        'sensor_controls': controlsensors,
        'points': list(values)
    })
    config.save()
    return redirect(url_for('index'))


@app.route('/get_rules')
def get_rules():
    return render_template('rules.html', rules=config.config['user'], config=config.config['devices'])


@app.route('/get_sensors')
def get_temps():
    # Get all the control sensors from config to disable slider
    controls = [control['sensor_controls'] for control in config.config['user'] if control['enabled']]
    controls = [value for values in controls for value in values]
    return render_template('sensors.html', sensors_list=(config.sensors_control, config.sensors_fan, config.sensors_temp), controls=controls)


@app.route('/get_sensor_values')
def get_sensor_values():
    sensors_list = {}
    sensors = {**config.sensors_control, **config.sensors_fan, **config.sensors_temp}
    for ident, sensor in sensors.items():
        sensors_list[ident] = sensor.Value
    # Get all the control sensors from config to disable slider
    controls = [control['sensor_controls'] for control in config.config['user'] if control['enabled']]
    controls = [value for values in controls for value in values]
    data = {'sensors': sensors_list, 'controls': controls}
    return data


@app.route('/set_controls', methods=['POST'])
def set_controls():
    ident = request.form['ident']
    speed = int(request.form['speed'])
    ident = ident.replace('slider', '')
    config.sensors_control[ident].Control.SetSoftware(speed)
    return str(speed)


@app.route('/delete_rule', methods=['POST'])
def delete_rule():
    index = int(request.form['delete'])
    set_default(index)
    config.config['user'].pop(index)
    config.save()
    return '200'


@app.route('/toggle_rule', methods=['POST'])
def disable_rule():
    index = int(request.form['toggle'])
    to_set = request.form['enable']
    if to_set == 'true':
        to_set = True
    else:
        to_set = False
    config.config['user'][index]['enabled'] = to_set
    config.save()
    set_default(index)
    return '200'


@app.route('/stop_controls', methods=['POST'])
def stop_controls():
    ident = request.form['ident']
    ident = ident.replace('stop', '')
    config.sensors_control[ident].Control.SetDefault()
    return '200'


@app.route('/rename_sensor', methods=['POST'])
def rename_sensor():
    ident = request.form['ident']
    new_name = request.form['name']
    config.config['devices'][ident] = new_name
    config.save()
    return '200'


@app.route('/set_option', methods=['POST'])
def set_option():
    option = request.form['option']
    value = request.form['value']
    if value == 'true':
        to_set = True
    else:
        to_set = False
    config.config['main'][option] = to_set
    config.save()
    return '200'


def set_default(index):
    for ident in config.config['user'][index]['sensor_controls']:
        config.sensors_control[ident].Control.SetDefault()


def close(systray):
    config.terminate = True
    config.stop()
    os._exit(0)  # Needed, so flask exits -.-


def open_browser(systray):
    b = webbrowser.get('windows-default')
    b.open('http://localhost:9876')


if config_moved:
    notify.init(str(Path.joinpath(folder, 'favicon.ico')), open_browser(None))
    notify.notify('Your config file was broken. I renamed it to config.jsoncorrupt.json!',
                  'SuckControl', str(Path.joinpath(folder, 'favicon.ico')), False, 10,
                  notify.dwInfoFlags.NIIF_USER | notify.dwInfoFlags.NIIF_LARGE_ICON)
    notify.uninit()
menu_options = (('Open', None, open_browser),)
systray = SysTrayIcon(str(Path.joinpath(folder, 'favicon.ico')), 'SuckControl', menu_options, on_quit=close)
systray.start()
serve(app, port=9876)
