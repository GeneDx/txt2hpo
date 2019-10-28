import spacy
import pickle
import configparser
from phenner.build_tree import build_search_tree, update_progress, hpo
from nltk.stem import RegexpStemmer
from phenner.config import logger, config
from phenner.spellcheck import spellcheck

try:
    nlp = spacy.load("en_core_web_sm", disable=["tagger", "parser", "ner"])
except OSError:
    logger.info('Performing a one-time download of an English language model for the spaCy POS tagger\n')
    from spacy.cli import download
    download('en')
    nlp = spacy.load("en_core_web_sm", disable=["tagger", "parser", "ner"])

nlp.vocab["first"].is_stop = False
nlp.vocab["second"].is_stop = False
nlp.vocab["third"].is_stop = False
nlp.vocab["fourth"].is_stop = False
nlp.vocab["fifth"].is_stop = False

st = RegexpStemmer('ing$|e$|able$|ic$|ia$|ity$', min=6)
max_search = 30

try:
    with open(config.get('tree', 'parsing_tree'), 'rb') as fh:
        terms = pickle.load(fh)

except (FileNotFoundError, TypeError, configparser.NoSectionError) as e:
    logger.info(f'Parsed search tree not found\n {e}')
    terms = build_search_tree()
    with open(config.get('tree', 'parsing_tree'), 'wb') as fh:
        pickle.dump(terms, fh)


def search_hp(tokens):
    """
    search for phenotypes within a list of tokens
    :param tokens: list of word tokens
    :return: list of hpo ids
    """
    results = []
    if not tokens:
        return results
    token = tokens[0]
    for i in range(len(tokens) + 1):
        if not token in terms:
            return results
        else:
            if not i in terms[token]:
                continue
            else:
                try_term = ' '.join(sorted(tokens[:i]))
                if try_term in terms[token][i].keys():
                    results += terms[token][i][try_term]
    return results


def extract_hpos(text, correct_spelling=True):
    """
    extracts hpo terms from text
    :param text: text
    :param correct_spelling:(True,False) attempt to correct spelling using spellcheck
    :return: list of phenotypes
    """
    hpos = []
    subsets = []
    if correct_spelling:
        text = spellcheck(text)

    tokens = nlp(text)
    tokens = [st.stem(x.lemma_.lower()) for x in tokens if not x.is_stop and not x.is_punct]

    for i, word in enumerate(tokens):
        try:
            subset = tokens[i:max_search + i]
        except IndexError:
            subset = tokens[i:]

        hpos += search_hp(subset)

        subsets.append(subset)

    return hpos


def self_evaluation():
    total = 0
    correct = 0
    wrong = []

    print("")
    logger.info('Running self evaluation, this may take a few minutes \n')
    i = 0
    n_nodes = len(hpo.nodes)

    for node in hpo:
        total += 1
        term = hpo.nodes[node]['name']
        hpids = extract_hpos(term, correct_spelling=False)
        if str(node) in hpids:
            correct += 1
        else:
            wrong.append(dict(
                actual=node,
                actual_name=term,
                extracted=hpids,
                extracted_name=[hpo.nodes[x]['name'] for x in hpids],
            ))

        i += 1
        progress = i / n_nodes
        update_progress(progress)

    logger.info('Done \n')

    logger.info(f"{(correct/total)*100} percent correct, {len(wrong)} items wrong")
    return wrong

