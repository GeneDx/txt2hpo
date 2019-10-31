from phenner.config import logger

from nltk.stem import RegexpStemmer
import spacy
import os
import sys

from phenopy import config as phenopy_config
from phenopy.obo import restore



network_file = os.path.join(phenopy_config.data_directory, 'hpo_network.pickle')
hpo = restore(network_file)

st = RegexpStemmer('ing$|e$|able$|ic$|ia$|ity$|al$|ly$', min=6)

try:
    nlp = spacy.load("en_core_web_sm", disable=["tagger", "parser", "ner"])
except OSError:
    logger.info('Performing a one-time download of an English language model for the spaCy POS tagger\n')
    from spacy.cli import download
    download('en')
    nlp = spacy.load("en_core_web_sm", disable=["tagger", "parser", "ner"])

remove_from_stops = "first second third fourth fifth under over front back behind ca below without no not "
remove_from_stops += "out up side right left more less during than take"
for not_a_stop in remove_from_stops.split(" "):
    nlp.vocab[not_a_stop].is_stop = False
    nlp.vocab[not_a_stop.capitalize()].is_stop = False


def build_search_tree():
    """
    Build stemmed, search tree for phenotypes / n-grams
    :param hpo: hpo object from phenopy
    :return: nested dictionary
    """
    terms = {}
    print("")
    logger.info('Building a stemmed parse tree, this may take a few seconds, dont worry this is a one time thing \n')
    i = 0
    n_nodes = len(hpo.nodes)

    for node in hpo:
        term = hpo.nodes[node]['name']
        if 'synonyms' in hpo.nodes[node]:
            synonyms = hpo.nodes[node]['synonyms']

        else:
            synonyms = []

        names = [term] + synonyms

        # extend names using custom rules
        extended_names = []
        for name in names:

            extended_names.append(name)
            extended_names.append(name.replace('Abnormality', 'Disorder'))

        for name in extended_names:

            tokens = nlp(name)
            tokens = [st.stem(st.stem(x.lemma_.lower())) for x in tokens if not x.is_stop and not x.is_punct]
            for token in tokens:
                if token not in terms:
                    terms[token] = {}
                if len(tokens) not in terms[token]:
                    terms[token][len(tokens)] = {}
                name_identifier = ' '.join(sorted(tokens))
                if name_identifier not in terms[token][len(tokens)]:
                    terms[token][len(tokens)][name_identifier] = [node]
                elif node not in terms[token][len(tokens)][name_identifier]:
                    terms[token][len(tokens)][name_identifier].append(node)

        i += 1
        progress = i/n_nodes
        update_progress(progress)
    logger.info('Done \n')

    return terms


def update_progress(progress):
    # https: // stackoverflow.com / a / 15860757
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

