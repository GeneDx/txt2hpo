from gensim.models import KeyedVectors
from txt2hpo.config import config


def load_model():
    if 'doc2vec' in config['models']:
        wv = KeyedVectors.load(config['models']['doc2vec'])
    return wv
