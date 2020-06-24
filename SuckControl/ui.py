import sys
import cli_ui as ui
from suckcontrol import *
from usersetup import *
from configcontrol import *


def show_menu(handle, config, sensors_all):
    choices = {'Add new rule': 'add', 'List Hardware Sensors': 'list_sensors', 'List Config Rules': 'list_config', 'Remove one rule': 'remove', 'Stop controlling the fans': 'stop', 'Reset your config': 'reset', 'Exit': 'exit'}
    pick = ui.ask_choice('Interactive Mode. Use --daemon after setting up.', choices=list(choices.keys()), sort=False)
    ui.debug(pick)
    if choices[pick] == 'add':
        config = add(config, sensors_all)
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
            ui.warning('Wrong number. Nothing deleted.')
        config_save(config)
    elif choices[pick] == 'stop':
        # Stop controlling the fans
        stopped = ui.ask_yes_no('Answer \'y\' after you stopped all instances!', default=False)
        if stopped:
            stop(handle)
    elif choices[pick] == 'reset':
        # Generate new empty config
        sure = ui.ask_yes_no('This will erase your config! Are you sure?', default=False)
        if sure:
            config_init(sensors_all)
    elif choices[pick] == 'exit':
        sys.exit(0)
    config = config_load()
    show_menu(handle, config, sensors_all)


config = config_load()
handle = initialize_lhm()
sensors_all = get_hardware_sensors(handle, config)
if config:
    try:
        param = sys.argv[1]
    except IndexError:
        param = None
    if param == '--daemon':
        start(handle, config, sensors_all)
        # if start() aborts cause of an error
        show_menu(handle, config, sensors_all)
    else:
        show_menu(handle, config, sensors_all)
else:
    config_init(sensors_all)
    show_menu(handle, config, sensors_all)
