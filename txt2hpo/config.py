import configparser
import logging
import os
from gensim.models import KeyedVectors
from txt2hpo import __project__, __version__

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

if not os.path.isfile(os.path.join(config_directory, 'txt2hpo.ini')):
    # create config
    config = configparser.ConfigParser()

    config['tree'] = {
        'parsing_tree': os.path.join(
            data_directory,
            'parsing_tree.pkl',
        ),
    }
    config['models'] = {}
    d2v_path = os.path.join(os.path.dirname(__file__), 'data/doc2vec_dm0_tagUniq_ep51_sa1e-05_vs40_ws18_mc5_neg5.wv.gz')
    d2v_vw_path = os.path.join(data_directory, 'doc2vec.wv')
    wv = KeyedVectors.load(d2v_path)
    wv.save(d2v_vw_path)
    config['models']['doc2vec'] = d2v_vw_path

    config['data'] = {}
    spellcheck_vocab_path = os.path.join(os.path.dirname(__file__), 'data/spellcheck_vocab_upd032020.json')
    config['data']['spellcheck_vocab'] = spellcheck_vocab_path

    with open(os.path.join(config_directory, 'txt2hpo.ini'), 'w') as configfile:
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
