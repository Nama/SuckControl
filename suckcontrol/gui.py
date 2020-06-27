import webview
import sys
from time import sleep
from suckcontrol import *
from usersetup import *
from configcontrol import *
import cli_ui as ui
from os import path, getcwd

from flask import Flask, render_template, request
import webview
import threading

folder = path.join(getcwd(), 'html')
app = Flask(__name__, static_folder=folder, template_folder=folder)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1


def show_menu(handle, config, sensors_all):
    config_show(config)

    choices = {'Add new rule': 'add', 'List Hardware Sensors': 'list_sensors', 'List Config Rules': 'list_config', 'Remove one rule': 'remove', 'Stop controlling the fans': 'stop', 'Reset your config': 'reset', 'Exit': 'exit'}
    pick = ui.ask_choice('Interactive Mode. Use --daemon after setting up.', choices=list(choices.keys()), sort=False)
    ui.debug(pick)
    if choices[pick] == 'add':
        config = usersetup.add(config, sensors_all)
        if config:
            config_save(config)
    elif choices[pick] == 'list_sensors':
        # List all temperature and control sensores
        data = []
        for ident, sensor in sensors_all.items():
            data.append(((ui.bold, config['main'][ident]), (ui.bold, sensor.Value)))
        ui.info_table(data, headers=['Name', 'Value'])
    elif choices[pick] == 'list_config':
        # Show the config
        config_show(config)
    elif choices[pick] == 'remove':
        config_show(config)
        remove = ui.ask_string('Enter the number of the rule you want to remove:')
        try:
            config['user'].pop(int(remove))
        except IndexError:
            ui.info('Wrong number. Nothing deleted.')
        config_save(config)
    elif choices[pick] == 'stop':
        # Stop controlling the fans
        stopped = ui.ask_yes_no('Answer \'y\' after you stopped all instances!', default=False)
        if stopped:
            stop(handle)
    elif choices[pick] == 'reset':
        # Generate new empty config
        sure = ui.ask_yes_no('This will erase your config! Are you sure?', default=False)
        if sure:
            config_init(sensors_all)
    elif choices[pick] == 'exit':
        sys.exit(0)
    config = config_load()
    show_menu(handle, config, sensors_all)


@app.route('/set_controls', methods=['POST', 'GET'])
def set_controls():
    sensorname = request.form['sensorname']
    speed = request.form['speed']
    ui.debug(sensorname, speed)
    for sensor in sensors_all.values():
        if sensor.SensorType == 7 and sensorname == sensor.Name:
            ui.debug(sensor.Name)
            try:
                sensor.Control.SetSoftware(speed)
            except AttributeError:
                ui.debug('Can\'t control this.')
    return speed


@app.route('/stop_controls')
def stop_controls():
    stop(handle)
    return '200'


@app.route('/test_controls')
def test_controls():
    html = []
    for sensor in sensors_all.values():
        ident = str(sensor.Identifier)
        sensor.set_Name(config['main'][ident.replace('/', '')])
        if sensor.SensorType == 7:
            html.append(sensor)
    return render_template('test_controls.html', html=html)


@app.route('/minimize')
def minimize():
    window.minimize()
    window.load_url('http://localhost')
    return 'minimized'


@app.route('/close')
def close():
    stop(handle)
    window.destroy()
    sys.exit(0)


@app.route('/template_sensors')
def template_sensors():
    sensors_all = get_hardware_sensors(handle, config)
    return render_template('sensors.html', sensors_all=sensors_all)


@app.route('/')
def index():
    if config:
        rules = config_show(config)
        return render_template('index.html', rules=rules, sensors_all=sensors_all)
    else:
        show_menu(handle, config, sensors_all)
    #else:
    #    config_init(sensors_all)
    #    show_menu(handle, config, sensors_all)


def start_server():
    app.run(host='localhost', port=80)
    while True:
        sleep(1)
        window.load_url('http://localhost')


if __name__ == '__main__':
    config = config_load()
    handle = initialize_lhm()
    sensors_all = get_hardware_sensors(handle, config)
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    window = webview.create_window('SuckControl', 'http://localhost', frameless=True, min_size=(1190, 740))
    webview.start(gui='cef', debug=True)
    sys.exit()
