import clr
import sys
import cli_ui as ui
from json import dump, load, loads
from json.decoder import JSONDecodeError
from os import path, getcwd
from shutil import move


class Config:
    def __init__(self):
        self.path = 'config.json'

        #if config:
        #    self.config = config
#       #     self.save()
        #else:
        #    self.config = None
        #    #ui.debug('Loading config')
        #    #self.load()

    def set_name(self, ident, sensor):
        pass

    def save(self, config):
        self.config = config
        with open(self.path, 'w') as configfile:
            dump(self.config, configfile, sort_keys=True, indent=4)
            ui.info_1('Config saved.')
            configfile.close()

    def load(self, handle=None):
        try:
            with open(self.path, 'r') as configfile:
                self.config = load(configfile)
                ui.debug('Config loaded')
                configfile.close()
                return self.config
        except FileNotFoundError:
            ui.info_1('No config found. Creating new one.')
            ui.info_3('Nothing\'s deleted if you cancel now.')
        except JSONDecodeError:
            ui.info_1('Corrupted config. Creating new one.')
            move(self.path, self.path + 'corrupt.json')
        self.config = None
        return self.init(handle)

    def init(self, handle):
        sensors_all, *sensors_list = get_hardware_sensors(handle, self.config)
        ui.debug('Creating new config')
        self.config = {'main': {}, 'user': []}
        for sensor in sensors_all.items():
            self.config['main'][sensor[0]] = sensor[1].Name
        self.save(self.config)
        return self.config

    def get_rules(self):
        rules = []
        if not self.config['user']:
            return None
        for i, rule in enumerate(self.config['user']):
            ui.debug(rule)
            data = []
            for temp, control in rule['points']:
                ui.debug(temp, control)
                data.append([(ui.bold, temp), (ui.bold, control)])
            rules.append((data, self.config['main'][rule['sensor_temp']], self.config['main'][rule['sensor_control']]))
        return rules


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


def get_hardware_sensors(handle, config, configcontrol=None):
    sensors_all = {}
    sensors_temp = {}
    sensors_fan = {}
    sensors_control = {}
    for hw in handle.Hardware:
        hw.Update()
        for sensor in hw.Sensors:
            if sensor.SensorType in (2, 5, 7):
                ident = str(sensor.Identifier).replace('/', '')
                sensors_all[ident] = sensor
                if sensor.SensorType == 2:
                    sensors_temp[ident] = sensor
                elif sensor.SensorType == 5:
                    sensors_fan[ident] = sensor
                elif sensor.SensorType == 7:
                    sensors_control[ident] = sensor
                try:
                    sensor.set_Name(config['main'][ident])
                # TODO: test with invalid identifiers in config
                except KeyError:
                    config['main'][ident] = sensor.Name
                except TypeError:
                    pass
        for shw in hw.SubHardware:
            shw.Update()
            for sensor in shw.Sensors:
                if sensor.SensorType in (2, 5, 7):
                    ident = str(sensor.Identifier).replace('/', '')
                    sensors_all[ident] = sensor
                    if sensor.SensorType == 2:
                        sensors_temp[ident] = sensor
                    elif sensor.SensorType == 5:
                        sensors_fan[ident] = sensor
                    elif sensor.SensorType == 7:
                        sensors_control[ident] = sensor
                    try:
                        sensor.set_Name(config['main'][ident])
                    except KeyError:
                        config['main'][ident] = sensor.Name
                    except TypeError:
                        pass
    if configcontrol:
        ui.debug('Saving from get_hardware_sensors')
        configcontrol.save(config)
    return sensors_all, sensors_temp, sensors_fan, sensors_control


def update_hardware_sensors(handle):
    for hw in handle.Hardware:
        hw.Update()
        for shw in hw.SubHardware:
            shw.Update()
