import json
from gensim.models import KeyedVectors
from txt2hpo.config import config


def load_model():
    if 'doc2vec' in config['models']:
        wv = KeyedVectors.load(config['models']['doc2vec'])
    return wv


def load_spellcheck_vocab():
    if 'spellcheck_vocab' in config['data']:
        with open(config['data']['spellcheck_vocab'], "rt") as fh:
            spellcheck_vocab = json.load(fh)
    return spellcheck_vocab
