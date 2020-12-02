import webview
import logging
import threading
from os import path, getcwd
from configcontrol import Config
from daemon import start_daemons
from flask import Flask, render_template, request

folder = path.join(getcwd(), 'html')
app = Flask(__name__, static_folder=folder, template_folder=folder)
flask_log = logging.getLogger('werkzeug')
flask_log.setLevel(logging.WARNING)
#flask_log.disabled = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
logging.basicConfig(filename='suckcontrol.log', format='%(asctime)s %(levelname)s %(funcName)s %(lineno)d: %(message)s', level=logging.DEBUG)
# TODO: https://plotly.com/python/click-events/


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add_rule')
def add_rule():
    return render_template('add_rule.html', sensors_all=config.sensors_all)


@app.route('/minimize')
def minimize():
    # TODO: shouldnt be needed
    window.minimize()
    window.load_url('http://localhost')
    return 'minimized'


@app.route('/get_rules')
def get_rules():
    rules = []
    for i, rule in enumerate(config.config['user']):
        data = []
        for temp, control in rule['points']:
            data.append([temp, control])
        rules.append((data, config.config['main'][rule['sensor_temp']], config.config['main'][rule['sensor_control']]))
    return render_template('rules.html', rules=rules, sensors_all=config.sensors_all)


@app.route('/get_sensors')
def get_temps():
    return render_template('sensors.html', sensors_all=config.sensors_all, sensors_list=(config.sensors_control, config.sensors_fan, config.sensors_temp))


@app.route('/test_controls')
def test_controls():
    html = []
    for sensor in config.sensors_all.values():
        ident = str(sensor.Identifier)
        sensor.set_Name(config.config['main'][ident.replace('/', '')])
        if sensor.SensorType == 7:
            html.append(sensor)
    return render_template('test_controls.html', html=html)


@app.route('/set_controls', methods=['POST', 'GET'])
def set_controls():
    sensorname = request.form['sensorname']
    speed = request.form['speed']
    for sensor in config.sensors_all.values():
        if sensor.SensorType == 7 and sensorname == sensor.Name:
            try:
                sensor.Control.SetSoftware(speed)
            except AttributeError:
                logging.warning('Can\'t control this.')
    return speed


@app.route('/stop_controls')
def stop_controls():
    config.stop()
    return '200'


def update_sensors():
    # TODO: shouldnt be needed
    sensors_all = config.update_hardware_sensors()
    return sensors_all


def close():
    config.terminate = True
    config.stop()
    window.destroy()


def start_server():
    app.run(host='localhost', port=80)


def start_gui():
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    # TODO: https://pystray.readthedocs.io/en/latest/usage.html
    global window
    window = webview.create_window('SuckControl', 'http://localhost', frameless=False, min_size=(1190, 740))
    window.closed += close
    webview.start(gui='cef', debug=True)
    #webview.start(gui='edgechromium', debug=True)


config = Config()
config.load()
start_daemons(config)
start_gui()
