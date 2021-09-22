import clr
import sys
import logging
from shutil import move
from pathlib import Path
from json import dump, load
from json.decoder import JSONDecodeError
from artemisremotecontrol import setleds

logger = logging.getLogger('suckcontrol.config')


class Config:
    def __init__(self):
        try:
            self.root_path = sys._MEIPASS
        except AttributeError:
            self.root_path = Path.cwd()
        self.terminate = False
        self.handle = self._initialize_lhm()
        self.path = 'config.json'
        self.sensors_all = {}
        self.sensors_control = {}
        self.sensors_fan = {}
        self.sensors_temp = {}
        self.artemis_counter = 0
        self.config = None
        self.config_template = {
            'main': {
                'artemis': False
            },
            'devices': {},
            'user': []
        }

    def save(self):
        with open(self.path, 'w') as configfile:
            dump(self.config, configfile, sort_keys=True, indent=4)
            logger.info('Config saved.')
            configfile.close()

    def load(self):
        moved = False
        try:
            with open(self.path, 'r') as configfile:
                self.config = load(configfile)
                logger.info('Config loaded')
                configfile.close()
                new_config = dict(self.config_template, **self.config)
                self.config = new_config
                self.save()
                return moved
        except FileNotFoundError:
            logger.info('No config found.')
        except JSONDecodeError:
            logger.warning('Corrupted config.')
            move(self.path, self.path + 'corrupt.json')
            moved = True
        self.config = None
        self._init()
        return moved

    def _init(self):
        # Creating new config file
        logger.info('Creating new config')
        self.config = self.config_template
        self.get_hardware_sensors()
        for sensor in self.sensors_all.items():
            self.config['devices'][sensor[0]] = sensor[1].Name
        self.save()

    def _initialize_lhm(self):
        lhm_file = str(Path(self.root_path, 'LibreHardwareMonitorLib.dll'))
        clr.AddReference(lhm_file)
        from LibreHardwareMonitor import Hardware
        handle = Hardware.Computer()
        handle.IsMotherboardEnabled = True
        handle.IsControllerEnabled = True
        handle.IsGpuEnabled = True
        handle.IsCpuEnabled = True
        handle.IsStorageEnabled = True
        handle.IsNetworkEnabled = True
        handle.IsMemoryEnabled = True
        handle.Open()
        return handle

    def stop(self):
        for hw in self.handle.Hardware:
            hw.Close()
            for shw in hw.SubHardware:
                shw.Close()

    def _in_config(self, sensor, ident):
        saved = None
        changed = False
        try:
            sensor.set_Name(self.config['devices'][ident])
            saved = True
        except KeyError:
            saved = False
        except TypeError:
            logger.debug('TypeError')
            pass

        if not saved:
            self.config['devices'][ident] = sensor.Name
            changed = True

        return changed

    def _put_hardware_config(self, sensor):
        ident = str(sensor.Identifier).replace('/', '')
        if sensor.SensorType == 4:
            self.sensors_temp[ident] = sensor
        elif sensor.SensorType == 7:
            self.sensors_fan[ident] = sensor
        elif sensor.SensorType == 9:
            self.sensors_control[ident] = sensor
        self.sensors_all[ident] = sensor

        changed = self._in_config(sensor, ident)
        return changed

    def get_hardware_sensors(self):
        changed = False
        artemis_hardware = {}
        artemis_network_index = 0
        for hw in self.handle.Hardware:
            hw.Update()
            for sensor in hw.Sensors:
                if sensor.SensorType in (4, 5, 9, 14):
                    if sensor.SensorType == 14:
                        artemis_hardware[sensor.Name + str(artemis_network_index)] = sensor.Value
                        artemis_network_index += 1
                    else:
                        artemis_hardware[sensor.Name] = sensor.Value
                if sensor.SensorType in (4, 7, 9):
                    changed = self._put_hardware_config(sensor)
                    if changed:
                        logger.info('Saving from get_hardware_sensors')
                        self.save()
            for shw in hw.SubHardware:
                shw.Update()
                for sensor in shw.Sensors:
                    if sensor.SensorType in (4, 5, 9, 14):
                        if sensor.SensorType == 14:
                            artemis_hardware[sensor.Name + str(artemis_network_index)] = sensor.Value
                            artemis_network_index += 1
                        else:
                            artemis_hardware[sensor.Name] = sensor.Value
                    if sensor.SensorType in (4, 7, 9,):
                        changed = self._put_hardware_config(sensor)
                        if changed:
                            logger.info('Saving from get_hardware_sensors')
                            self.save()
        if self.config['main']['artemis'] and self.artemis_counter == 1:
            setleds('SuckControl', artemis_hardware)
            self.artemis_counter = 0
        self.artemis_counter += 1
