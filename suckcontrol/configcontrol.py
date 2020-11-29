import clr
import sys
import logging
from json import dump, load
from json.decoder import JSONDecodeError
from os import path, getcwd
from shutil import move


class Config:
    def __init__(self):
        self.terminate = False
        self.handle = self.initialize_lhm()
        self.path = 'config.json'
        self.config = None
        self.sensors_all = {}
        self.sensors_control = {}
        self.sensors_fan = {}
        self.sensors_temp = {}

    def set_name(self, ident, sensor):
        pass

    def save(self):
        with open(self.path, 'w') as configfile:
            dump(self.config, configfile, sort_keys=True, indent=4)
            logging.debug('Config saved.')
            configfile.close()

    def load(self):
        try:
            with open(self.path, 'r') as configfile:
                self.config = load(configfile)
                logging.debug('Config loaded')
                configfile.close()
                return self.config
        except FileNotFoundError:
            # TODO: Ask in gui to create new config.
            logging.debug('No config found. Creating new one.')
            logging.debug('Nothing\'s deleted if you cancel now.')
        except JSONDecodeError:
            logging.debug('Corrupted config. Creating new one.')
            move(self.path, self.path + 'corrupt.json')
        self.config = None
        self.init()

    def init(self):
        # Creating new config file
        logging.debug('Creating new config')
        self.config = {'main': {}, 'user': []}
        self.get_hardware_sensors()
        for sensor in self.sensors_all.items():
            self.config['main'][sensor[0]] = sensor[1].Name
        self.save()

    def initialize_lhm(self):
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

    def stop(self):
        for hw in self.handle.Hardware:
            hw.Close()
            for shw in hw.SubHardware:
                shw.Close()

    def get_hardware_sensors(self):
        changed = False
        for hw in self.handle.Hardware:
            hw.Update()
            for sensor in hw.Sensors:
                if sensor.SensorType in (2, 5, 7):
                    ident = str(sensor.Identifier).replace('/', '')
                    self.sensors_all[ident] = sensor
                    if sensor.SensorType == 2:
                        self.sensors_temp[ident] = sensor
                    elif sensor.SensorType == 5:
                        self.sensors_fan[ident] = sensor
                    elif sensor.SensorType == 7:
                        self.sensors_control[ident] = sensor
                    try:
                        sensor.set_Name(self.config['main'][ident])
                    # TODO: test with invalid identifiers in config
                    except KeyError:
                        self.config['main'][ident] = sensor.Name
                        changed = True
                    except TypeError:
                        pass
            for shw in hw.SubHardware:
                shw.Update()
                for sensor in shw.Sensors:
                    if sensor.SensorType in (2, 5, 7):
                        ident = str(sensor.Identifier).replace('/', '')
                        self.sensors_all[ident] = sensor
                        if sensor.SensorType == 2:
                            self.sensors_temp[ident] = sensor
                        elif sensor.SensorType == 5:
                            self.sensors_fan[ident] = sensor
                        elif sensor.SensorType == 7:
                            self.sensors_control[ident] = sensor
                        try:
                            sensor.set_Name(self.config['main'][ident])
                        except KeyError:
                            self.config['main'][ident] = sensor.Name
                            changed = True
                        except TypeError:
                            pass
        if changed:
            logging.debug('Saving from get_hardware_sensors')
            self.save()

    def update_hardware_sensors(self):
        for hw in self.handle.Hardware:
            hw.Update()
            for shw in hw.SubHardware:
                shw.Update()
