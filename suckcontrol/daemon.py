import logging
from time import sleep
from numpy import interp
from threading import Thread

logger = logging.getLogger('suckcontrol.daemon')


def _control_speed(config, temp, controls, points):
    sensors_all = config.sensors_all
    try:
        sensor_temp = sensors_all[temp]
    except KeyError:
        logger.warning(f'{temp} doesn\'t exists.')
        return
    sensor_controls = []
    for control in controls:
        try:
            sensor_controls.append(sensors_all[control])
        except KeyError:
            logger.warning(f'{control} doesn\'t exists.')
            continue
    if not len(sensor_controls):
        # No sensors to control, abort
        return
    to_set = None
    temp_value = int(sensor_temp.Value)
    control_value = int(sensor_controls[0].Value)
    logger.debug(f'Fan: {sensor_controls[0].Name}')

    logger.debug(f'Temp: {temp_value}')
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
                logger.debug(f'{point}, {points[nextpoint]}')
                point_next = points[nextpoint]
                if temp_value in range(point[0], point_next[0]):
                    # Temp is between point[0] and point_next[0]
                    xp = [point[0], point_next[0]]
                    fp = [point[1], point_next[1]]
                    to_set = interp(temp_value, xp, fp)
                    break
    logger.debug(f'Before change: {control_value} - After change: {to_set}')
    if control_value == to_set or to_set is None:
        # No need to set
        return
    for control in sensor_controls:
        try:
            control.Control.SetSoftware(to_set)
        except AttributeError:
            logger.warning('Can\'t control this sensor: {control.Name} - {control.Identifier}')
            return
    return


def _update_rules(config):
    while True:
        # Update rules, for newly added ones
        sleep(0.1)  # Incase there are no rules.
        config.get_hardware_sensors()
        for rule in config.config['user']:
            sleep(0.2)
            if config.terminate:
                break
            if not rule['enabled']:
                continue
            temp = rule['sensor_temp']
            controls = rule['sensor_controls']
            points = rule['points']
            # Make the fans suck
            _control_speed(config, temp, controls, points)
        if config.terminate:
            break


def start_daemons(config):
    update_rules = Thread(target=_update_rules, args=(config,))
    update_rules.daemon = True
    update_rules.start()
    logger.debug('daemon-thread started')
