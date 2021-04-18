import clr
import sys
import logging
from json import dump, load
from json.decoder import JSONDecodeError
from os import path, getcwd
from shutil import move

try:
    root_path = sys._MEIPASS
except AttributeError:
    root_path = getcwd()


def nvapiw():
    nvapiw_file = path.join(root_path, 'NvAPIWrapper.dll')
    clr.AddReference(nvapiw_file)
    from NvAPIWrapper import GPU
    return GPU.PhysicalGPU.GetPhysicalGPUs()


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
            logging.debug('No config found. Creating new one.')
        except JSONDecodeError:
            # TODO: Tell in gui old config is renamed to corrupt.json.
            logging.warning('Corrupted config. Creating new one.')
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
        lhm_file = path.join(root_path, 'LibreHardwareMonitorLib.dll')
        clr.AddReference(lhm_file)
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

    def in_config(self, sensor, ident, nvidia):
        saved = None
        changed = False
        try:
            if not nvidia:
                sensor.set_Name(self.config['main'][ident])
                saved = True
            else:
                if ident in self.config['main']:
                    saved = True
        # TODO: test with invalid identifiers in rules in config
        except KeyError:
            saved = False
        except TypeError:
            logging.debug('TypeError')
            pass

        if not saved:
            if not nvidia:
                self.config['main'][ident] = sensor.Name
            else:
                try:
                    self.config['main'][ident] = self.sensors_fan[ident]['Name']
                except KeyError:
                    self.config['main'][ident] = self.sensors_control[ident]['Name']
            changed = True

        return changed

    def put_hardware_config(self, sensor):
        try:
            ident = str(sensor.Identifier).replace('/', '')
            nvidia = False
        except AttributeError:
            nvidia = True
        if not nvidia:
            if sensor.SensorType == 3:
                self.sensors_temp[ident] = sensor
            elif sensor.SensorType == 7:
                self.sensors_fan[ident] = sensor
            elif sensor.SensorType == 9:
                self.sensors_control[ident] = sensor
            self.sensors_all[ident] = sensor
            changed = self.in_config(sensor, ident, nvidia)
        else:
            for i, gpu in enumerate(sensor):
                for cooler in gpu.CoolerInformation.Coolers:
                    sensor = cooler
                    ident = f'gpu{i}control{cooler.CoolerId}'
                    if ident in self.config['main']:
                        name = self.config['main'][ident]
                    else:
                        name = f'GPU #{i} Control #{cooler.CoolerId}'
                    self.sensors_control[ident] = {
                        'Identifier': ident,
                        'Name': name,
                        'Value': cooler.CurrentLevel,
                        'SensorType': 9,
                        'SetSoftware': gpu.CoolerInformation.SetCoolerSettings,
                        'CoolerID': cooler.CoolerId
                    }
                    self.sensors_all[ident] = self.sensors_control[ident]
                    self.in_config(sensor, ident, nvidia)
                    ident = f'gpu{i}fan{cooler.CoolerId}'
                    if ident in self.config['main']:
                        name = self.config['main'][ident]
                    else:
                        name = f'GPU #{i} Fan #{cooler.CoolerId}'
                    self.sensors_fan[ident] = {
                        'Identifier': ident,
                        'Name': name,
                        'Value': cooler.CurrentFanSpeedInRPM,
                        'SensorType': 7,
                        'SetSoftware': gpu.CoolerInformation.SetCoolerSettings,
                        'CoolerID': cooler.CoolerId
                    }
                    self.sensors_all[ident] = self.sensors_fan[ident]
                    changed = self.in_config(sensor, ident, nvidia)
        return changed

    def get_hardware_sensors(self):
        changed = False
        nvidia = False
        for hw in self.handle.Hardware:
            hw.Update()
            for sensor in hw.Sensors:
                if sensor.SensorType in (3, 7, 9):
                    if 'gpu-nvidia' in str(sensor.Identifier) and 'control' in str(sensor.Identifier):
                        # Don't add the control sensor, but the temp sensor
                        nvidia = True
                        continue
                    changed = self.put_hardware_config(sensor)
            for shw in hw.SubHardware:
                shw.Update()
                for sensor in shw.Sensors:
                    if sensor.SensorType in (3, 7, 9):
                        changed = self.put_hardware_config(sensor)

        if nvidia:
            gpus = nvapiw()
            #for gpu in gpus:
                #logging.debug(f'GPU: {gpu.FullName} {gpu.GPUId}')
            changed = self.put_hardware_config(gpus)
                #for m, cooler in enumerate(gpu.CoolerInformation.Coolers):
                #    logging.debug(f'Cooler {cooler.CoolerId} {cooler.CurrentFanSpeedInRPM}, {cooler.CurrentLevel}')

        if changed:
            logging.debug('Saving from get_hardware_sensors')
            self.save()

    def update_hardware_sensors(self):  # trash?
        for hw in self.handle.Hardware:
            hw.Update()
            for shw in hw.SubHardware:
                shw.Update()
