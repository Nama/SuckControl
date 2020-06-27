import cli_ui as ui
from usersetup import *
from json import dump, load

configpath = 'config.json'


def config_save(config):
    with open(configpath, 'w') as configfile:
        dump(config, configfile, sort_keys=True, indent=4)
        ui.info_1('Config saved. Restart other instances if there are any!')


def config_load():
    try:
        configfile = open(configpath, 'rb')
        config = load(configfile)
        ui.debug('Config loaded')
    except FileNotFoundError:
        ui.info_1('No config found. Creating new one.')
        ui.info_3('Nothing\'s deleted if you cancel now.')
        config = None
    return config


def config_init(sensors_all):
    ui.debug('Creating new config')
    ui.info_1('Hi, please read the instructions on https://github.com/Nama/SuckControl')
    config = {'main': {}, 'user': []}
    config = set_sensor_names(config, sensors_all)
    config = add(config, sensors_all)
    if config:
        config_save(config)
    else:
        ui.warning('First time setup got aborted')
        config_init(sensors_all)


def config_show(config):
    rules = []
    for i, rule in enumerate(config['user']):
        ui.debug(rule)
        data = []
        for temp, control in rule['points']:
            ui.debug(temp, control)
            data.append([(ui.bold, temp), (ui.bold, control)])
        #ui.info_1('Rule #{}'.format(i))
        #ui.info_table(data, headers=(config['main'][rule['sensor_temp']], config['main'][rule['sensor_control']]))
        rules.append((data, config['main'][rule['sensor_temp']], config['main'][rule['sensor_control']]))
    return rules
