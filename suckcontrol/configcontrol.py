import cli_ui as ui
from usersetup import add, set_sensor_names
from json import dump, load

configpath = 'config.json'


class Config:
    def __init__(self, config=None):
        self.path = 'config.json'
        if config:
            self.config = config
            self.save()
        else:
            self.load()

    def save(self):
        with open(configpath, 'w') as configfile:
            dump(self.config, configfile, sort_keys=True, indent=4)
            ui.info_1('Config saved. Restart other instances if there are any!')
            self.load()

    def load(self):
        try:
            configfile = open(self.path, 'rb')
            self.config = load(configfile)
            ui.debug('Config loaded')
        except FileNotFoundError:
            ui.info_1('No config found. Creating new one.')
            ui.info_3('Nothing\'s deleted if you cancel now.')
            self.config = None
        return self.config

    def init(self, sensors_all):
        ui.debug('Creating new config')
        ui.info_1('Hi, please read the instructions on https://github.com/Nama/SuckControl')
        self.config = {'main': {}, 'user': []}
        self.config = set_sensor_names(self.config, sensors_all)
        config = add(self.config, sensors_all)
        if config:
            self.save()
        else:
            ui.warning('First time setup got aborted')
            self.init(sensors_all)

    def show(self, config):
        rules = []
        for i, rule in enumerate(self.config['user']):
            ui.debug(rule)
            data = []
            for temp, control in rule['points']:
                ui.debug(temp, control)
                data.append([(ui.bold, temp), (ui.bold, control)])
            rules.append((data, config['main'][rule['sensor_temp']], config['main'][rule['sensor_control']]))
        return rules
