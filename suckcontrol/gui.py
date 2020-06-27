from sys import exit
import webview
import threading
import cli_ui as ui
from time import sleep
from os import path, getcwd
from usersetup import *
from configcontrol import Config
from flask import Flask, render_template, request, session

folder = path.join(getcwd(), 'html')
app = Flask(__name__, static_folder=folder, template_folder=folder)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1


@app.route('/')
def index():
    return gui.cindex()


@app.route('/close')
def close():
    return gui.cclose()


@app.route('/minimize')
def minimize():
    return gui.cminimize()


@app.route('/template_sensors')
def template_sensors():
    return gui.ctemplate_sensors()


@app.route('/test_controls')
def test_controls():
    return gui.ctest_controls()


@app.route('/set_controls', methods=['POST', 'GET'])
def set_controls():
    sensorname = request.form['sensorname']
    speed = request.form['speed']
    return gui.cset_controls(sensorname, speed)


@app.route('/stop_controls')
def stop_controls():
    return gui.cstop_controls()


class Gui:
    def __init__(self, handle, config, sensors_all):
        self.handle = handle
        self.config = config
        self.sensors_all = sensors_all
        self.window = None

    def window(self, window):
        self.window(window)

    def cindex(self):
        rules = Config().show(self.config)
        return render_template('index.html', rules=rules, sensors_all=self.sensors_all)

    def cclose(self):
        stop(self.handle)
        self.window.destroy()
        sys.exit(0)

    def cminimize(self):
        self.window.minimize()
        self.window.load_url('http://localhost')
        return 'minimized'

    def ctemplate_sensors(self):
        sensors_all = get_hardware_sensors(self.handle, self.config)
        return render_template('sensors.html', sensors_all=sensors_all)

    def ctest_controls(self):
        html = []
        for sensor in self.sensors_all.values():
            ident = str(sensor.Identifier)
            sensor.set_Name(self.config['main'][ident.replace('/', '')])
            if sensor.SensorType == 7:
                html.append(sensor)
        return render_template('test_controls.html', html=html)

    def cstop_controls(self):
        stop(self.handle)
        return '200'

    def cset_controls(self, sensorname, speed):
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
    window = webview.create_window('SuckControl', 'http://localhost', frameless=True, min_size=(1190, 740))
    gui.window = window
    webview.start(gui='cef', debug=True)
    exit()


config = Config().load()
handle = initialize_lhm()
sensors_all = get_hardware_sensors(handle, config)
gui = Gui(handle, config, sensors_all)


def get_data():
    return handle, config, sensors_all, gui
