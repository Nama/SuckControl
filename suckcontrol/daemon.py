import logging
from time import sleep
from numpy import interp
from threading import Thread

terminate = False


def _control_speed(config, temp, control, points, naw):
    sensors_all = config.sensors_all
    sensor_temp = sensors_all[temp]
    sensor_control = sensors_all[control]
    to_set = None
    temp_value = int(sensor_temp.Value)
    control_value = int(sensor_control.Value)
    logging.debug(f'Fan: {sensor_control.Name}')
    logging.debug(f'Temp: {temp_value}')
    if temp_value < points[0][0]:
        # Temp is below first point
        to_set = points[0][1]
    else:
        for i, point in enumerate(points):
            # Check, if this is the last point
            if point == points[-1]:
                # Temp is above last point
                to_set = point[1]
            else:
                nextpoint = i + 1
                logging.debug(f'{point}, {points[nextpoint]}')
                point_next = points[nextpoint]
                if temp_value in range(point[0], point_next[0]):
                    # Temp is between point[0] and point_next[0]
                    xp = [point[0], point_next[0]]
                    fp = [point[1], point_next[1]]
                    to_set = interp(temp_value, xp, fp)
                    break
    logging.debug(f'Before change: {control_value} - After change: {to_set}')
    if control_value == to_set or to_set is None:
        # No need to set
        return naw
    try:
        sensor_control.Control.SetSoftware(to_set)
    except AttributeError:
        logging.debug(f'Can\'t control this sensor: {sensor_control.Name} - {sensor_control.Identifier}')
        # NvAPIWrapper fallback - LHM can't control turing (and newer?)
        hw_ident = str(sensor_control.Identifier).split('/')
        if not hw_ident[1] == 'gpu-nvidia':
            return naw
        gpu_fan_set = False
        logging.debug(f'Nvidia GPU detected')
        if not naw:
            from configcontrol import nvapiw
            naw = nvapiw()
            logging.debug('NvAPIWrapper Loaded')
        for i, gpu in enumerate(naw):
            # This approach is not nice - need a way to identify LHM <-> NvAPIW controls
            logging.debug(f'GPU: {gpu} {i} {hw_ident}')
            if hw_ident[2] == str(i):
                # Trying to make it work with multiple GPUs
                for m, cooler in enumerate(gpu.CoolerInformation.Coolers):
                    # Set all fans of the GPU to that speed
                    gpu.CoolerInformation.SetCoolerSettings(m + 1, int(to_set))  # IDs start at 1
                gpu_fan_set = True
                logging.debug('Nvidia fan speed set')
            if gpu_fan_set:
                break
    return naw


def _update_rules(config):
    naw = None
    running_rules = []
    while True:
        # Update rules, for newly added ones
        sleep(0.1)  # Incase there are no rules.
        config.get_hardware_sensors()
        for rule in config.config['user']:
            sleep(0.2)
            if config.terminate:
                break
            config.update_hardware_sensors()
            temp = rule['sensor_temp']
            running_rules.append(temp)
            control = rule['sensor_control']
            points = rule['points']
            # Make the fans suck
            #naw = _control_speed(config, temp, control, points, naw)
            #controller = Thread(target=_control_speed, args=(config, temp, control, points))
            #controller.start()
        if config.terminate:
            break


def _update_hw(config):
    while True:
        sleep(0.1)
        # Update the sensor values
        config.get_hardware_sensors()
        if config.terminate:
            break


def start_daemons(config):
    update_rules = Thread(target=_update_rules, args=(config,))
    update_rules.start()
    logging.debug('daemon-threads started')
    #update_hw = Thread(target=_update_hw, args=(config,))
    #update_hw.start()
