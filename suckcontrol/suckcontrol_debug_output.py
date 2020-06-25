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
    if sensor.SensorType in (2, 7):
        if sensor.SensorType == 2:
            stype = 'Temp'
        else:
            stype = 'Cont'
            try:
                sensor.Control.SetSoftware(100)
                sleep(2)
                sensor.Control.SetDefault()
            except:
                print('Couldn\'t control ' + sensor.Name)
        print(stype, sensor.Name, sensor.Value, sensor.Identifier)


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
