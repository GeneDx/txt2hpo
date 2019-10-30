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

# log project and version
logger.info(f'{__project__} {__version__}')


# create config directory if it doesn't exist
config_directory = os.path.join(os.environ.get('HOME'), f'.{__project__}')
project_directory = os.path.abspath(__project__)
project_data_dir = os.path.join(project_directory, 'data')
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

# create config
config = configparser.ConfigParser()

if not os.path.isfile(os.path.join(config_directory, 'phenner.ini')):
    # create config
    config = configparser.ConfigParser()

    config['tree'] = {
        'parsing_tree': os.path.join(
            data_directory,
            'parsing_tree.pkl',
        ),

    }
    config['spellcheck'] = {
        'vocabulary': os.path.join(
            project_data_dir,
            'spellcheck_vocab.json',
        ),

    }
    with open(os.path.join(config_directory, 'phenner.ini'), 'w') as configfile:
        logger.info('writing config file to: %s '%config_directory)
        config.write(configfile)

else:
    # read config
    config_file = os.environ.get(
        f'{__project__.upper()}_CONFIG',
        os.path.join(config_directory, f'{__project__}.ini', )
    )

    config.read(config_file)
    logger.info(f'Using configuration file: {config_file}')

