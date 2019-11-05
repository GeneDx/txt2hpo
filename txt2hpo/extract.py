
import json
from txt2hpo.build_tree import update_progress, hpo_network
from txt2hpo.config import logger
from txt2hpo.spellcheck import spellcheck
from txt2hpo.nlp import nlp
from txt2hpo.nlp import st
from txt2hpo.build_tree import search_tree


def group_sequence(lst):
    """
    Break a sequence of integers into continuous groups
    [1,2,3,5,7,8] -> [[1,2,3],[5],[7,8]]
    :param lst: list of ints
    :return: list of lists
    """
    grouped = [[lst[0]]]
    for i in range(1, len(lst)):
        if lst[i - 1] + 1 == lst[i]:
            grouped[-1].append(lst[i])
        else:
            grouped.append([lst[i]])
    return grouped


def hpo(text, correct_spelling=True, max_neighbors=5):

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

    stemmed_tokens = [st.stem(st.stem(x.lemma_.lower())) for x in tokens]

    phenotokens = []
    phenindeces = []

    # index phenotype tokens by matching each stem against root of search tree
    for i, token in enumerate(stemmed_tokens):
        if token in search_tree:
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
        grp_phen_tokens = [x.text for x in grp_phen_tokens if not x.is_stop and not x.is_punct]

        # sort to match same order as used in making keys for search tree
        try_term_key = ' '.join(sorted(grp_phen_tokens))

        # attempt to extract hpo terms from tree based on root, length of phrase and key
        try:
            hpids = search_tree[grp_phen_tokens[0]][len(grp_phen_tokens)][try_term_key]

        except:
            hpids = []

        # if found any hpids, append to extracted
        if hpids:
            if len(phen_group) == 1:
                matched_string = tokens[phen_group[0]]
                start = tokens[phen_group[0]].idx
                end = start + len(tokens[phen_group[0]])
            else:
                matched_string = tokens[min(phen_group):max(phen_group)+1]
                start = tokens[phen_group[0]:phen_group[-1]+1].start_char
                end = tokens[phen_group[0]:phen_group[-1]+1].end_char

            extracted_terms.append({"hpid":hpids, "index":[start, end], "matched":matched_string.text})
    if extracted_terms:
        return json.dumps(extracted_terms)
    else:
        return []


def self_evaluation(correct_spelling=False):
    total = 0
    correct = 0
    wrong = []

    print("")
    logger.info('Running self evaluation, this may take a few minutes \n')
    i = 0
    n_nodes = len(hpo_network.nodes)

    for node in hpo_network:
        total += 1
        term = hpo_network.nodes[node]['name']
        hpids = []
        extracted = hpo(term, correct_spelling=correct_spelling)
        if extracted:
            extracted = json.loads(extracted)

            for item in extracted:
                hpids += item['hpid']

            if str(node) in hpids:
                correct += 1
            else:
                wrong.append(dict(
                    actual=node,
                    actual_name=term,
                    extracted=hpids,
                    extracted_name=[hpo_network.nodes[x]['name'] for x in hpids],
                ))
        else:
            wrong.append(dict(
                actual=node,
                actual_name=term,
                extracted=[],
                extracted_name=[],
            ))

        i += 1
        progress = i / n_nodes
        update_progress(progress)

    logger.info('Done \n')

    logger.info(f"{(correct/total)*100} percent correct, {len(wrong)} items wrong")
    return wrong

