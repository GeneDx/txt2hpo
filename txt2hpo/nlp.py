import spacy
from txt2hpo.config import logger
from nltk.stem import RegexpStemmer
from txt2hpo.config import config

try:
    nlp = spacy.load("en_core_web_sm", disable=["tagger", "parser", "ner"])
except OSError:
    logger.info('Performing a one-time download of an English language model for the spaCy POS tagger\n')
    from spacy.cli import download
    download('en')
    nlp = spacy.load("en_core_web_sm", disable=["tagger", "parser", "ner"])


# these are used in hpo as part of phenotype definition, should block from filtering
remove_from_stops = "first second third fourth fifth under over front back behind ca below without no not "
remove_from_stops += "out up side right left more less during than take move full"
for not_a_stop in remove_from_stops.split(" "):
    nlp.vocab[not_a_stop].is_stop = False
    nlp.vocab[not_a_stop.capitalize()].is_stop = False

st = RegexpStemmer('ing$|e$|able$|ic$|ia$|ity$|al$|ly$', min=7)


def load_model():
    if 'doc2vec' in config['models']:
        from gensim.parsing.preprocessing import remove_stopwords
        from gensim.utils import simple_preprocess as preprocess
        logger.info("Loaded doc2vec model")
        return gensim.models.doc2vec.Doc2Vec.load(config['models']['doc2vec'])
