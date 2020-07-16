from sys import exit
import webview
import threading
import cli_ui as ui
from time import sleep
from os import path, getcwd
from configcontrol import *
from flask import Flask, render_template, request, session

folder = path.join(getcwd(), 'html')
app = Flask(__name__, static_folder=folder, template_folder=folder)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
# TODO: go thru all imports, use "import *" if possible
# TODO: check if the functions need _ as a prefix
# TODO: https://plotly.com/python/click-events/


@app.route('/')
def index():
    return gui.index()


@app.route('/add_rule')
def add_rule():
    return render_template('add_rule.html', sensors_all=sensors_all)


@app.route('/close')
def close():
    return gui.close()


@app.route('/minimize')
def minimize():
    return gui.minimize()


@app.route('/get_rules')
def get_rules():
    return gui.get_rules()


@app.route('/get_sensors')
def get_temps():
    return gui.get_sensors()


@app.route('/test_controls')
def test_controls():
    return gui.test_controls()


@app.route('/set_controls', methods=['POST', 'GET'])
def set_controls():
    sensorname = request.form['sensorname']
    speed = request.form['speed']
    return gui.set_controls(sensorname, speed)


@app.route('/stop_controls')
def stop_controls():
    return gui.stop_controls()


class Gui:
    def __init__(self, handle, config, sensors_all, sensors_list):
        self.handle = handle
        self.config = config
        self.sensors_all = sensors_all
        self.sensors_list = sensors_list
        self.window = None

    def window(self, window):
        self.window(window)

    def update_sensors(self):
        sensors_all = update_hardware_sensors(self.handle)
        return sensors_all

    def index(self):
        return render_template('index.html')

    def close(self):
        stop(self.handle)
        self.window.destroy()
        sys.exit(0)

    def minimize(self):
        self.window.minimize()
        self.window.load_url('http://localhost')
        return 'minimized'

    def get_rules(self):
        rules = configcontrol.get_rules()
        return render_template('rules.html', rules=rules, sensors_all=self.sensors_all)

    def get_sensors(self):
        self.update_sensors()
        return render_template('sensors.html', sensors_all=self.sensors_all, sensors_list=self.sensors_list)

    def test_controls(self):
        html = []
        for sensor in self.sensors_all.values():
            ident = str(sensor.Identifier)
            sensor.set_Name(self.config['main'][ident.replace('/', '')])
            if sensor.SensorType == 7:
                html.append(sensor)
        return render_template('test_controls.html', html=html)

    def stop_controls(self):
        stop(self.handle)
        return '200'

    def set_controls(self, sensorname, speed):
        ui.debug(sensorname, speed)
        for sensor in self.sensors_all.values():
            if sensor.SensorType == 7 and sensorname == sensor.Name:
                ui.debug(sensor.Name)
                try:
                    sensor.Control.SetSoftware(speed)
                except AttributeError:
                    ui.debug('Can\'t control this.')
        return speed


def start_server():
    app.run(host='localhost', port=80)


def start(gui):
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    #settings.update({
    #    'no-proxy-server': True
    #})
    # TODO: https://pystray.readthedocs.io/en/latest/usage.html
    window = webview.create_window('SuckControl', 'http://localhost', frameless=True, min_size=(1190, 740))
    gui.window = window
    webview.start(gui='cef', debug=True)
    exit()


def get_data():
    return handle, config, sensors_all, gui


handle = initialize_lhm()
configcontrol = Config()
config = configcontrol.load(handle)
sensors_all, *sensors_list = get_hardware_sensors(handle, config, configcontrol)
print(sensors_list[0])
#configcontrol.save(config)
gui = Gui(handle, config, sensors_all, sensors_list)
