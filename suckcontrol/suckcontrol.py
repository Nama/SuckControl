import webbrowser
import logging
from waitress import serve
from pathlib import Path
from configcontrol import Config
from daemon import start_daemons
import notify
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
logging.basicConfig(filename='suckcontrol.log', format='%(asctime)s %(levelname)s %(funcName)s %(lineno)d: %(message)s', level=logging.WARNING)

# TODO: Function to rename sensors
# TODO: Remove Test Controls site
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add_rule')
def add_rule():
    # Get all the control sensors from config to hide them
    controls = [control['sensor_controls'] for control in config.config['user']]
    controls = [value for values in controls for value in values]
    return render_template('add_rule.html', sensors_all=config.sensors_all, controls=controls)


@app.route('/save_rule', methods=['POST'])
def save_rule():
    data = request.json
    flask_log.debug(data)
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
    controls = [control['sensor_controls'] for control in config.config['user']]
    controls = [value for values in controls for value in values]
    return render_template('sensors.html', sensors_list=(config.sensors_control, config.sensors_fan, config.sensors_temp), controls=controls)


@app.route('/test_controls')
def test_controls():
    html = []
    for sensor in config.sensors_control.values():
        html.append(sensor)
    return render_template('test_controls.html', html=html)


@app.route('/set_controls', methods=['POST'])
def set_controls():
    sensorname = request.form['sensorname']
    speed = int(request.form['speed'])
    for sensor in config.sensors_control.values():
        try:
            if sensorname == sensor.Name:
                sensor.Control.SetSoftware(speed)
        except AttributeError:
            if sensorname == sensor['Name']:
                sensor['SetSoftware'](sensor['CoolerID'], speed)
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


def close(systray):
    config.terminate = True
    config.stop()
    #systray.shutdown()


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
