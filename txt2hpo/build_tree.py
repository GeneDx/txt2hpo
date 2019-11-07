import configparser
import pickle
import sys
from txt2hpo.config import logger, config
from txt2hpo.nlp import nlp
from txt2hpo.nlp import st
from phenopy.config import config as phenopy_config

from phenopy import generate_annotated_hpo_network


obo_file = phenopy_config.get('hpo', 'obo_file')

disease_to_phenotype_file = phenopy_config.get('hpo', 'disease_to_phenotype_file')

hpo_network, alt2prim, disease_records = \
    generate_annotated_hpo_network(obo_file,
                                   disease_to_phenotype_file,
                                   annotations_file=None,
                                   ages_distribution_file=None
                                   )

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
    n_nodes = len(hpo_network.nodes)

    for node in hpo_network:
        term = hpo_network.nodes[node]['name']
        if 'synonyms' in hpo_network.nodes[node]:
            synonyms = hpo_network.nodes[node]['synonyms']

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

try:
    with open(config.get('tree', 'parsing_tree'), 'rb') as fh:
        search_tree = pickle.load(fh)

except (FileNotFoundError, TypeError, configparser.NoSectionError) as e:
    logger.info(f'Parsed search tree not found\n {e}')
    search_tree = build_search_tree()
    with open(config.get('tree', 'parsing_tree'), 'wb') as fh:
        pickle.dump(search_tree, fh)