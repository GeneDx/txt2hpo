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


# these are used in hpo as part of phenotype definition, should keep them
nlp.vocab["first"].is_stop = False
nlp.vocab["second"].is_stop = False
nlp.vocab["third"].is_stop = False
nlp.vocab["fourth"].is_stop = False
nlp.vocab["fifth"].is_stop = False

nlp.vocab["side"].is_stop = False
nlp.vocab["right"].is_stop = False
nlp.vocab["left"].is_stop = False
nlp.vocab["front"].is_stop = False
nlp.vocab["more"].is_stop = False
nlp.vocab["less"].is_stop = False
nlp.vocab["during"].is_stop = False
nlp.vocab["than"].is_stop = False
nlp.vocab["take"].is_stop = False

st = RegexpStemmer('ing$|e$|able$|ic$|ia$|ity$|al$', min=6)
max_search = 30

try:
    with open(config.get('tree', 'parsing_tree'), 'rb') as fh:
        terms = pickle.load(fh)

except (FileNotFoundError, TypeError, configparser.NoSectionError) as e:
    logger.info(f'Parsed search tree not found\n {e}')
    terms = build_search_tree()
    with open(config.get('tree', 'parsing_tree'), 'wb') as fh:
        pickle.dump(terms, fh)


def group_sequence(lst):
    res = [[lst[0]]]
    for i in range(1, len(lst)):
        if lst[i - 1] + 1 == lst[i]:
            res[-1].append(lst[i])
        else:
            res.append([lst[i]])
    return res


def extract_hpos(text, correct_spelling=True, max_neighbors=5):

    """
    extracts hpo terms from text
    :param text: text
    :param correct_spelling:(True,False) attempt to correct spelling using spellcheck
    :param max_neighbors:(int) max number of phenotypic groups to attempt to search for a matching phenotype
    :return: list of phenotypes
    """


    if correct_spelling:
        text = spellcheck(text)

    tokens = nlp(text)

    stemmed_tokens = [st.stem(x.lemma_.lower()) for x in tokens]

    phenotokens = []
    phenindeces = []

    # index phenotype tokens by matching each stem against root of search tree
    for i, token in enumerate(stemmed_tokens):
        if token in terms:
            phenotokens.append(token)
            phenindeces.append(i)

    extracted_terms = []

    if not phenindeces:
        return extracted_terms

    groups = group_sequence(phenindeces)
    phen_groups = []

    # Add individual word token indices to phenotype groups
    phen_groups += [[x] for x in phenindeces]

    # Assemble adjacent groups of phenotypes into groups of various sizes
    for i in range(len(groups)):
        if groups[i] not in phen_groups:
            phen_groups.append(groups[i])

        # make sure not to modify original groups object
        adjacent_groups = groups[i].copy()
        for j in range(1, max_neighbors):
            if len(groups) > i+j:
                adjacent_groups += groups[i+j]
                if adjacent_groups not in phen_groups:
                    phen_groups.append(adjacent_groups)

    for phen_group in phen_groups:
        # if there is only one phenotype in a group
        if len(phen_group) == 1:
            grp_phen_tokens = stemmed_tokens[phen_group[0]]

        # if multiple phenotypes, get all words between
        else:
            grp_phen_tokens = " ".join(stemmed_tokens[min(phen_group):max(phen_group)+1])

        # remove stop words and punctuation from group of phenotypes
        grp_phen_tokens = nlp(grp_phen_tokens)
        grp_phen_tokens = [str(x) for x in grp_phen_tokens if not x.is_stop and not x.is_punct]

        # sort to match same order as used in making keys for search tree
        try_term_key = ' '.join(sorted(grp_phen_tokens))

        # attempt to extract hpo terms from tree based on root, length of phrase and key
        try:
            hpids = terms[grp_phen_tokens[0]][len(grp_phen_tokens)][try_term_key]

        except:
            hpids = []

        # if found any hpids, append to extracted
        if hpids:
            if len(phen_group) == 1:
                matched_string = tokens[phen_group[0]]
            else:
                matched_string = tokens[min(phen_group):max(phen_group)+1]
            extracted_terms.append(dict(hpid=hpids, index=phen_group, matched=str(matched_string)))

    return extracted_terms


def self_evaluation(correct_spelling=False):
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
        hpids = []
        extracted = extract_hpos(term, correct_spelling=correct_spelling)

        for item in extracted:
            hpids += item['hpid']

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

