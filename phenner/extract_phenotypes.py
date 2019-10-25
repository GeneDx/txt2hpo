import spacy
import pickle
import configparser
from phenner.build_tree import build_search_tree
from nltk.stem import RegexpStemmer
from phenner.config import logger, config
from phenner.spellcheck import spellcheck

try:
    nlp = spacy.load('en')
except OSError:
    logger.info('Performing a one-time download of an English language model for the spaCy POS tagger\n')
    from spacy.cli import download
    download('en')
    nlp = spacy.load('en')

st = RegexpStemmer('ing$|e$|able$|ic$|ia$|ity$', min=6)
max_search = 5

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
                    results.append(terms[token][i][try_term])
    return results


def extract_hpos(text, correct_spelling=True):
    """
    extracts hpo terms from text
    :param text: text
    :param correct_spelling:(True,False) attempt to correct spelling using spellcheck
    :return: list of phenotypes
    """
    hpo = []
    if correct_spelling:
        text = spellcheck(text)

    for i, word in enumerate(text.split()):
        try:
            subset = text.split()[i:max_search + i]
        except:
            subset = text.split()[i:]
        subset = [x for x in subset]
        subset = nlp(" ".join(subset))

        search_space = [st.stem(x.lemma_.lower()) for x in subset if not x.is_stop and not x.is_punct]

        hpo += search_hp(search_space)
    return hpo

