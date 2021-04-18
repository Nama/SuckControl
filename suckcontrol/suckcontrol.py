import webbrowser
import logging
from waitress import serve
from os import path, getcwd
from configcontrol import Config
from daemon import start_daemons
from flask import Flask, render_template, request
from infi.systray import SysTrayIcon

folder = path.join(getcwd(), 'html')
app = Flask(__name__, static_folder=folder, template_folder=folder)
flask_log = logging.getLogger('werkzeug')
flask_log.setLevel(logging.WARNING)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
logging.basicConfig(filename='suckcontrol.log', format='%(asctime)s %(levelname)s %(funcName)s %(lineno)d: %(message)s', level=logging.DEBUG)
# TODO: https://plotly.com/python/click-events/


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add_rule')
def add_rule():
    return render_template('add_rule.html', sensors_all=config.sensors_all)


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
    return render_template('sensors.html', sensors_list=(config.sensors_control, config.sensors_fan, config.sensors_temp))


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


@app.route('/stop_controls')
def stop_controls():
    # TODO: Stop only one device
    config.stop()
    return '200'


def close(systray):
    config.terminate = True
    config.stop()


def open_browser(systray):
    b = webbrowser.get('windows-default')
    b.open('http://localhost')


config = Config()
config.load()
start_daemons(config)

menu_options = (('Open', None, open_browser),)
systray = SysTrayIcon('favicon.ico', 'SuckControl', menu_options, on_quit=close)
systray.start()
serve(app, port=80)
