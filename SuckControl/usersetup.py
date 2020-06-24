import cli_ui as ui
from time import sleep


def set_sensor_names(config, sensors_all):
    ui.info_2('We need to give all sensors a name, so you can recognize them.')
    ui.info('Check the sensors in LHM first, to know them: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor')
    for ident, sensor in sensors_all.items():
        ui.debug(sensor.Name)
        lib_name = sensor.Name
        lib_hwpath = sensor.Identifier
        if sensor.SensorType == 2:
            temp = sensor.Value
            ui.info_1('The temperature is {}°C'.format(temp))
        elif sensor.SensorType == 7:
            ui.info_1('I set the speed to 100% for 5 seconds')
            try:
                sensor.Control.SetSoftware(100)
                sleep(5)
                sensor.Control.SetDefault()
            except AttributeError:
                ui.warning('Can\'t control {}'.format(sensor.Name))
        ui.info_2('Hardware string: {}'.format(lib_hwpath))
        user_name = ui.ask_string('Name this sensor: {}'.format(lib_name), default=lib_name)
        sensor.set_Name(user_name)
        config['main'][ident] = user_name
    return config


def add(config, sensors_all):
    pick = []
    choices_temps = {}
    choices_controls = {}
    for ident, sensor in sensors_all.items():
        name = config['main'][ident]
        if sensor.SensorType == 2:
            choices_temps[name] = ident
        elif sensor.SensorType == 7:
            choices_controls[name] = ident

    temp = ui.ask_choice('Choose the temperature sensor you want your fan depending on:', choices=list(choices_temps.keys()), sort=False)
    if not temp:
        ui.warning('Aborting. Nothing picked.')
        return None
    pick.append(choices_temps[temp])
    config['user'].append({'sensor_temp': pick[0]})
    control = ui.ask_choice('Choose the control sensor you want to control:', choices=list(choices_controls.keys()), sort=False)
    if not control:
        ui.warning('Aborting. Nothing picked.')
        return None
    pick.append(choices_controls[control])
    config['user'][-1]['sensor_control'] = pick[1]
    ui.info_1('You will be asked repeatedly to enter temperatures and fan speeds.')
    ui.info_3('First, enter the first point of your curve and press enter.')
    ui.info_3('Then the second one, And so on. Enter nothing and press enter if you are done.')
    answer = True
    ask = 'Enter one point of the temperatures (°C) and fan speeds (%) curve for the sensors {} and {}. In this format: "<temp>,<speed>":'
    config['user'][-1]['points'] = []
    while answer:
        answer = ui.ask_string(ask.format(config['main'][pick[0]], config['main'][pick[1]]))
        if answer:
            values = answer.split(',')
            vall = []
            for value in values:
                vall.append(int(value))
                if int(value) > 100:
                    ui.info_2('You can\'t enter values over 100')
                    continue
            config['user'][-1]['points'].append(vall)
    if not config['user'][-1]['points']:
        ui.warning('Didn\'t enter any values, not saving.')
        config['user'].pop()
    return config
