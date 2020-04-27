import configparser
import pickle
import sys
from txt2hpo.config import logger, config
from txt2hpo.util import hpo_network
from txt2hpo.nlp import nlp_sans_ner
from txt2hpo.nlp import st


def build_search_tree(custom_synonyms=None, masked_terms=None):
    """
    Build stemmed, search tree for phenotypes / n-grams
    :param hpo: hpo object from phenopy
    :param custom_synonyms: dictionary of hpo-id (key), list of synonyms (value)
    :param masked_terms: block specific hpids from parsing
    :return: nested dictionary
    """
    if custom_synonyms == None:
        custom_synonyms = {}

    if masked_terms == None:
        masked_terms = ['HP:0000001']
    else:
        masked_terms += ['HP:0000001']

    terms = {}
    logger.info('Building a stemmed parse tree, this may take a few seconds, dont worry this is a one time thing \n')

    for hpid, synonyms in custom_synonyms.items():
        if hpid in masked_terms:
            continue
        if hpid in hpo_network.nodes():
            if 'synonyms' in hpo_network.nodes[hpid]:
                hpo_network.nodes[hpid]['synonyms'] += synonyms
            else:
                hpo_network.nodes[hpid]['synonyms'] = synonyms

    i = 0
    n_nodes = len(hpo_network.nodes)

    for node in hpo_network:
        if node in masked_terms:
            continue
        term = hpo_network.nodes[node]['name']
        if 'synonyms' in hpo_network.nodes[node]:
            synonyms = hpo_network.nodes[node]['synonyms']
        else:
            synonyms = []

        names = [term] + synonyms

        # extend names using custom rules
        extended_names = []
        for name in names:
            name = name.replace(', ',' ')
            name = name.replace(',', ' ')
            extended_names.append(name.lower())
            extended_names.append(name.capitalize())
            extended_names.append(name.title())
            extended_names.append(name.replace('-',' '))
            extended_names.append(name.replace('Abnormality', 'Disorder'))

        for name in extended_names:

            tokens = nlp_sans_ner(name)
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

