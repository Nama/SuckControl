import cli_ui as ui
from gui import get_data, start
from time import sleep
from numpy import interp
from sys import exit, argv
from threading import Thread
from usersetup import *
from configcontrol import Config
from signal import signal, SIGINT

ui.CONFIG['verbose'] = False
ui.CONFIG['color'] = 'never'
terminate = False


def _control_speed(sensors_all, temp, control, points):
    sensor_temp = sensors_all[temp]
    sensor_control = sensors_all[control]
    while True:
        if terminate:
            exit()
        sleep(1.3)
        to_set = None
        temp_value = int(sensor_temp.Value)
        control_value = int(sensor_control.Value)
        if temp_value < points[0][0]:
            # Temp is below first point
            ui.debug('Too cold')
            to_set = points[0][1]
        else:
            for i, point in enumerate(points):
                # Check, if this is the last point
                if point == points[-1]:
                    # Temp is above last point
                    ui.debug('Too hot')
                    to_set = point[1]
                else:
                    next = i + 1
                    ui.debug(point, points[next])
                    point_next = points[next]
                    if temp_value in range(point[0], point_next[0]):
                        # Temp is between point[0] and point_next[0]
                        ui.debug(point)
                        xp = [point[0], point_next[0]]
                        fp = [point[1], point_next[1]]
                        to_set = interp(temp_value, xp, fp)
                        break
        ui.debug(sensor_control.Name, control_value, to_set)
        if control_value != to_set and to_set is not None:
            ui.debug(to_set)
            try:
                sensor_control.Control.SetSoftware(to_set)
            except AttributeError:
                ui.error('Can\'t control this sensor: {}'.format(sensor_control.Name))


def handler(signal_received, frame):
    # Since we can't get handle here, use terminate
    ui.info_1('Setting fans to default...')
    global terminate
    terminate = True


def daemon(handle, config, sensors_all):
    ui.debug('Config OK, I guess')
    signal(SIGINT, handler)
    for rule in config['user']:
        temp = rule['sensor_temp']
        control = rule['sensor_control']
        points = rule['points']
        controller = Thread(target=_control_speed, args=(sensors_all, temp, control, points))
        controller.start()
        sleep(0.5)
        #_control_speed(sensors_all, temp, control, points)
        ui.debug('daemon started')
    while True:
        sleep(1)
        if terminate:
            # Wait for SIGTERM
            stop(handle)
            ui.info_2('Exiting.')
            exit(0)


if __name__ == '__main__':
    #config = Config().load()
    #handle = initialize_lhm()
    #sensors_all = get_hardware_sensors(handle, config)
    handle, config, sensors_all, gui = get_data()
    #gui = Gui(handle, config, sensors_all)
    if config:
        if len(config['user']) == 0:
            ui.error('No rules for fan speeds found. Add new rules.')
            # Start gui
            start(gui)
        try:
            param = argv[1]
        except IndexError:
            param = None
        if param == '--daemon':
            daemon(handle, config, sensors_all)
            # if start() aborts cause of an error
            start(gui)
        else:
            start(gui)
    else:
        Config().init(sensors_all)
        start(gui)
