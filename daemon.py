import clr
import sys
import cli_ui as ui
from time import sleep
from numpy import interp
from os import path, getcwd
from threading import Thread
from signal import signal, SIGINT

terminate = False


def initialize_lhm():
    try:
        lhm_path = sys._MEIPASS
    except AttributeError:
        lhm_path = getcwd()
    file = path.join(lhm_path, 'LibreHardwareMonitorLib.dll')
    clr.AddReference(file)
    from LibreHardwareMonitor import Hardware
    handle = Hardware.Computer()
    handle.IsMotherboardEnabled = True
    handle.IsControllerEnabled = True
    handle.IsGpuEnabled = True
    handle.IsCpuEnabled = True
    handle.IsStorageEnabled = True
    handle.Open()
    return handle


def stop(handle):
    for hw in handle.Hardware:
        hw.Close()
        for shw in hw.SubHardware:
            shw.Close()


def get_hardware_sensors(handle, config):
    sensors_all = {}
    for hw in handle.Hardware:
        hw.Update()
        for sensor in hw.Sensors:
            if sensor.SensorType in (2, 7):
                ident = str(sensor.Identifier).replace('/', '')
                sensors_all[ident] = sensor
                try:
                    sensor.set_Name(config['main'][ident])
                except TypeError:
                    pass
                ui.debug(sensor.Name)
        for shw in hw.SubHardware:
            shw.Update()
            for sensor in shw.Sensors:
                if sensor.SensorType in (2, 7):
                    ident = str(sensor.Identifier).replace('/', '')
                    sensors_all[ident] = sensor
                    try:
                        sensor.set_Name(config['main'][ident])
                    except TypeError:
                        pass
                    ui.debug(sensor.Name)
    return sensors_all


def _control_speed(sensors_all, temp, control, points):
    sensor_temp = sensors_all[temp]
    sensor_control = sensors_all[control]
    while True:
        if terminate:
            sys.exit()
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
                ui.info('Can\'t control this sensor: {}'.format(sensor_control.Name))


def handler(signal_received, frame):
    # Since we can't get handle here, use terminate
    ui.info_1('Setting fans to default...')
    global terminate
    terminate = True


def start(handle, config, sensors_all):
    if len(config['user']) == 0:
        ui.info_1('No rules for fan speeds found. Add new rules.')
        return
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
            sys.exit(0)
