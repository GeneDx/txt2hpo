import logging

import configparser
from phenner import __project__, __version__
import os

# create logger
logger = logging.getLogger(__project__)
logger.setLevel(logging.DEBUG)

# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# add the handler to the logger
logger.addHandler(ch)

# create config
config = configparser.ConfigParser()

# create config directory if it doesn't exist
config_directory = os.path.join(os.environ.get('HOME'), f'.{__project__}')
project_directory = os.path.abspath(__project__)

try:
    os.makedirs(config_directory)
except FileExistsError:
    pass

# create data directory if it doesn't exist
data_directory = os.path.join(config_directory, 'data')
try:
    os.makedirs(data_directory)
except FileExistsError:
    pass

if not os.path.isfile(os.path.join(config_directory, 'phenner.ini')):
    config['tree'] = {
        'parsing_tree': os.path.join(
            data_directory,
            'parsing_tree.pkl',
        ),

    }
    with open(os.path.join(config_directory, 'phenner.ini'), 'w') as configfile:
        logger.info('writing config file to: %s '%config_directory)
        config.write(configfile)

