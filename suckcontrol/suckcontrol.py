import os
import webbrowser
import logging
import notify
from waitress import serve
from pathlib import Path
from configcontrol import Config
from daemon import start_daemons
from flask import Flask, render_template, request, redirect, url_for
from infi.systray import SysTrayIcon

config = Config()
config_moved = config.load()
start_daemons(config)

folder = Path(config.root_path, 'html')
app = Flask(__name__, static_folder=str(folder), template_folder=str(folder))
flask_log = logging.getLogger('werkzeug')
flask_log.setLevel(logging.WARNING)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
logging.basicConfig(filename=str(Path(config.root_path, 'suckcontrol.log')), format='%(asctime)s %(levelname)s %(funcName)s %(lineno)d: %(message)s', level=logging.WARNING)


@app.route('/')
def index():
    # Get all the control sensors from config to disable slider
    controls = [control['sensor_controls'] for control in config.config['user'] if control['enabled']]
    controls = [value for values in controls for value in values]
    return render_template('index.html', rules=config.config['user'], config=config.config['main'], sensors_list=(config.sensors_control, config.sensors_fan, config.sensors_temp), controls=controls)


@app.route('/add_rule')
def add_rule():
    # Get all the control sensors from config to hide them
    controls = [control['sensor_controls'] for control in config.config['user']]
    controls = [value for values in controls for value in values]
    return render_template('add_rule.html', sensors_all=config.sensors_all, controls=controls)


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
    return render_template('rules.html', rules=config.config['user'], config=config.config['main'])


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
    to_delete = int(request.form['delete'])
    config.config['user'].pop(to_delete)
    config.save()
    config.stop()  # Removed controls will be "freed" again
    return '200'


@app.route('/toggle_rule', methods=['POST'])
def disable_rule():
    rule_index = int(request.form['toggle'])
    to_set = request.form['enable']
    if to_set == 'true':
        to_set = True
    else:
        to_set = False
    config.config['user'][rule_index]['enabled'] = to_set
    config.save()
    return '200'


@app.route('/stop_controls')
def stop_controls():
    config.stop()
    return '200'


@app.route('/rename_sensor', methods=['POST'])
def rename_sensor():
    ident = request.form['ident']
    new_name = request.form['name']
    config.config['main'][ident] = new_name
    config.save()
    return '200'


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
