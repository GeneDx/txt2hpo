import os
from gensim.models import KeyedVectors
from txt2hpo.config import logger


def load_model():
    model_path = os.path.join(os.path.dirname(__file__), 'doc2vec_dm0_tagUniq_ep51_sa1e-05_vs40_ws18_mc5_neg5.wv.gz')
    wv = KeyedVectors.load(model_path)
    logger.info("Loading doc2vec model")
    return wv