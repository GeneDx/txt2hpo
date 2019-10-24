
from phenner.config import logger
from nltk.stem import RegexpStemmer
import re
import spacy
import os
import sys
from phenopy import config as phenopy_config
from phenopy.obo import restore

network_file = os.path.join(phenopy_config.data_directory, 'hpo_network.pickle')
hpo = restore(network_file)

st = RegexpStemmer('ing$|e$|able$|ic$|ia$|ity$', min=6)

try:
    nlp = spacy.load('en')
except OSError:
    logger.info('Performing a one-time download of an English language model for the spaCy POS tagger\n')
    from spacy.cli import download
    download('en')
    nlp = spacy.load('en')

def build_search_tree():
    """
    Build stemmed, search tree for phenotypes / n-grams
    :param hpo: hpo object from phenopy
    :return: nested dictionary
    """
    terms = {}
    print("")
    logger.info('Building a stemmed parse tree, this may take a minute, dont worry this is a one time thing \n')
    i = 0
    n_nodes = len(hpo.nodes)
    for node in hpo:
        term = hpo.nodes[node]['name']
        if 'synonym' in hpo.nodes[node]:
            synonyms = hpo.nodes[node]['synonym']
        else:
            synonyms = ""
        synonyms = re.findall(r'"(.*?)"', ','.join(synonyms))
        names = [term] + synonyms
        for name in names:
            tokens = nlp(name)
            tokens = [x for x in tokens if not x.is_punct]
            tokens = [x for x in tokens if not x.is_stop]
            tokens = [st.stem(x.lemma_.lower()) for x in tokens]
            for token in tokens:
                if token not in terms:
                    terms[token] = {}
                if len(tokens) not in terms[token]:
                    terms[token][len(tokens)] = {}
                terms[token][len(tokens)][' '.join(sorted(tokens))] = node
        i += 1
        progress = i/n_nodes
        update_progress(progress)
    logger.info('Done \n')
    return terms


def update_progress(progress):
    barLength = 50 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength*progress))
    text = "\rProgress: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), round(progress*100, 1), status)
    sys.stdout.write(text)
    sys.stdout.flush()

