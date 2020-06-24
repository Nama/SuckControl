import sys
import usersetup
import daemon
import cli_ui as ui
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


def config_init():
    ui.debug('Creating new config')
    ui.info_1('Hi, please read the instructions on https://github.com/Nama/SuckControl')
    config = {'main': {}, 'user': []}
    config = usersetup.set_sensor_names(config, sensors_all)
    config = usersetup.add(config, sensors_all)
    if config:
        config_save(config)
    else:
        ui.debug('add() or set_sensor_names() got aborted')
        config_init()


def config_show(config):
    for i, rule in enumerate(config['user']):
        ui.debug(rule)
        data = []
        for temp, control in rule['points']:
            ui.debug(temp, control)
            data.append([(ui.bold, temp), (ui.bold, control)])
        ui.info_1('Rule #{}'.format(i))
        ui.info_table(data, headers=(config['main'][rule['sensor_temp']], config['main'][rule['sensor_control']]))


def show_menu(handle, config, sensors_all):
    choices = {'Add new rule': 'add', 'List Hardware Sensors': 'list_sensors', 'List Config Rules': 'list_config', 'Remove one rule': 'remove', 'Stop controlling the fans': 'stop', 'Reset your config': 'reset', 'Exit': 'exit'}
    pick = ui.ask_choice('Interactive Mode. Use --daemon after setting up.', choices=list(choices.keys()), sort=False)
    ui.debug(pick)
    if choices[pick] == 'add':
        config = usersetup.add(config, sensors_all)
        if config:
            config_save(config)
    elif choices[pick] == 'list_sensors':
        # List all temperature and control sensores
        data = []
        for ident, sensor in sensors_all.items():
            data.append(((ui.bold, config['main'][ident]), (ui.bold, sensor.Value)))
        ui.info_table(data, headers=['Name', 'Value'])
    elif choices[pick] == 'list_config':
        # Show the config
        config_show(config)
    elif choices[pick] == 'remove':
        config_show(config)
        remove = ui.ask_string('Enter the number of the rule you want to remove:')
        try:
            config['user'].pop(int(remove))
        except IndexError:
            ui.info('Wrong number. Nothing deleted.')
        config_save(config)
    elif choices[pick] == 'stop':
        # Stop controlling the fans
        stopped = ui.ask_yes_no('Answer \'y\' after you stopped all instances!', default=False)
        if stopped:
            daemon.stop(handle)
    elif choices[pick] == 'reset':
        # Generate new empty config
        sure = ui.ask_yes_no('This will erase your config! Are you sure?', default=False)
        if sure:
            config_init()
    elif choices[pick] == 'exit':
        sys.exit(0)
    config = config_load()
    show_menu(handle, config, sensors_all)


config = config_load()
handle = daemon.initialize_lhm()
sensors_all = daemon.get_hardware_sensors(handle, config)
if config:
    try:
        param = sys.argv[1]
    except IndexError:
        param = None
    if param == '--daemon':
        daemon.start(handle, config, sensors_all)
        # if start() aborts cause of an error
        show_menu(handle, config, sensors_all)
    else:
        show_menu(handle, config, sensors_all)
else:
    config_init()
    show_menu(handle, config, sensors_all)
