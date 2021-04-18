import clr, sys
from os import path, getcwd
from time import sleep


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
    handle.IsNetworkEnabled = False
    handle.Open()
    return handle


def get_sensors(sensor):
    if sensor.SensorType == 2:
        stype = ('Temp', '°C')
    elif sensor.SensorType == 5:
        stype = ('Fan', 'RPM')
    elif sensor.SensorType == 7:
        stype = ('Cont', '%')
        try:
            if sensor.Name == 'GPU Fan':
                #print(stype[0], sensor.Name, str(sensor.Value) + stype[1], sensor.Identifier)
                sensor.Control.SetSoftware(100)
                #print(stype[0], sensor.Name, str(sensor.Value) + stype[1], sensor.Identifier)
                sleep(20)
                sensor.Control.SetDefault()
                print(stype[0], sensor.Name, str(sensor.Value) + stype[1], sensor.Identifier)
        except:
            print('Couldn\'t control ' + sensor.Name)
    if sensor.SensorType in (2, 5, 7):
        print(stype[0], sensor.Name, str(sensor.Value) + stype[1], sensor.Identifier)


def fetch_temp(handle):
    for i, hw in enumerate(handle.Hardware):
        print('###############Hardware')
        hw.Update()
        for sensor in hw.Sensors:
            get_sensors(sensor)
        print('#######SubHardware')
        for subH in hw.SubHardware:
            subH.Update()
            for sensor in subH.Sensors:
                get_sensors(sensor)


HardwareHandle = initialize_lhm()
fetch_temp(HardwareHandle)
print('done')
input()
