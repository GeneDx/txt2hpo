import json
import numpy as np
from itertools import combinations, chain

from txt2hpo.build_tree import update_progress, hpo_network
from txt2hpo.config import logger
from txt2hpo.spellcheck import spellcheck
from txt2hpo.nlp import nlp, load_model, similarity_term_to_context
from txt2hpo.nlp import st
from txt2hpo.nlp import load_model
from txt2hpo.build_tree import search_tree


def group_sequence(lst):
    """
    Break a sequence of integers into continuous groups
    [1,2,3,5,7,8] -> [[1,2,3],[5],[7,8]]
    :param lst: list of ints
    :return: list of lists
    """
    if not lst:
        return []
    grouped = [[lst[0]]]
    for i in range(1, len(lst)):
        if lst[i - 1] + 1 == lst[i]:
            grouped[-1].append(lst[i])
        else:
            grouped.append([lst[i]])
    return grouped


def index_tokens(stemmed_tokens):
    """index phenotype tokens by matching each stem against root of search tree"""
    phenotokens = []
    phenindeces = []

    for i, token in enumerate(stemmed_tokens):
        if token in search_tree:
            phenotokens.append(token)
            phenindeces.append(i)

    return phenotokens, phenindeces


def assemble_groups(original, max_distance=2, min_compl=0.20):
    """
    Join adjacent groups of phenotypes into new groups
    [[1,2],[5,6]] -> {((1, 2), (5, 6)), (1, 2), (5, 6)}
    :param original: Original list of lists of integers
    :param max_distance: Maximum number of combinations
    :param min_compl: Minimum fraction of complete term
    :return: set of grouped tuple index sequences
    """

    def missing_elements(L):
        start, end = L[0], L[-1]
        return sorted(set(range(start, end + 1)).difference(L))

    ori_set = set(tuple(set(x)) for x in original)

    fused_set = set()
    final_set = set()
    fused_set_uniq = set()

    for distance in range(1, max_distance):
        combs = list(combinations(ori_set, distance))
        for comb in combs:
            fused_comb = tuple(set(np.concatenate(comb)))
            if fused_comb in ori_set:
                continue
            else:
                fused_set.add(tuple(set(comb)))

        for item in fused_set:
            if len(set(np.concatenate(item))) == len(np.concatenate(item)):
                sorted_seq = sorted(list(chain(*item)))
                gaps = missing_elements(sorted_seq)
                completeness = len(sorted_seq) / (len(sorted_seq) + len(gaps))
                if completeness >= min_compl:
                    fused_set_uniq.add(item)
        final_set = set(ori_set.union(fused_set_uniq))

    return final_set


def recombine_groups(group_indx, min_r_length=1, max_r_length=3):
    """
    Generate a set of all possible combinations for each group of indices
    {((1, 2), (5,)), (1, 2), (5,)} -> [[1, 2], [1], [2], [5], [1, 2, 5], [1, 5], [2, 5]]
    :param group_indx: set of tuples, output of assemble_groups
    :param min_r_length: minimum length of combinations
    :param max_r_length: maximum length of combinations
    :return: list of lists of indices
    """
    return_list = []
    for group in group_indx:
        for r_length in range(min_r_length, max_r_length):
            try:
                new_comb = sorted(list(np.concatenate(group)))
            except:
                new_comb = list(group)
            if new_comb not in return_list:
                return_list.append(new_comb)
            for new_mix_comb in list(combinations(new_comb, r_length)):
                new_mix_comb = sorted(new_mix_comb)
                if new_mix_comb not in return_list:
                    return_list.append(list(new_mix_comb))
    return return_list


def permute_leave_one_out(original_list, min_terms=1):
    """
    Supplement lists of iterables with groups where each of the items is left out
    :param original_list:
    :param min_terms:
    :return: supplemented list
    [['1','2','3']] -> [['1', '2', '3'], ['2', '3'], ['1', '3'], ['1', '2']]
    """
    permuted_list = original_list.copy()
    for group in original_list:
        if len(group) <= min_terms:
            continue
        for i, x in enumerate(group):
            permuted_group = group.copy()
            del permuted_group[i]
            if permuted_group not in permuted_list:
                permuted_list.append(permuted_group)
    return permuted_list


def find_hpo_terms(phen_groups, stemmed_tokens, tokens, base_index, context_window):
    """Match hpo terms from stemmed tree to indexed groups in text"""
    extracted_terms = []
    for phen_group in phen_groups:
        # if there is only one phenotype in a group
        if len(phen_group) == 1:
            grp_phen_tokens = stemmed_tokens[phen_group[0]]

        # if multiple phenotypes, get all words between
        else:
            grp_phen_tokens = " ".join(stemmed_tokens[min(phen_group):max(phen_group) + 1])

        # remove stop words and punctuation from group of phenotypes
        grp_phen_tokens = nlp(grp_phen_tokens)
        grp_phen_tokens = [x.text for x in grp_phen_tokens if not x.is_stop and not x.is_punct]

        # sort to match same order as used in making keys for search tree
        try_term_key = ' '.join(sorted(grp_phen_tokens))

        # attempt to extract hpo terms from tree based on root, length of phrase and key
        try:
            hpids = search_tree[grp_phen_tokens[0]][len(grp_phen_tokens)][try_term_key]

        except (KeyError, IndexError):
            hpids = []

        # if found any hpids, append to extracted
        if hpids:

            if len(phen_group) == 1:
                matched_string = tokens[phen_group[0]]
                start = tokens[phen_group[0]].idx
                end = start + len(tokens[phen_group[0]])

            else:
                matched_string = tokens[min(phen_group):max(phen_group) + 1]
                start = tokens[min(phen_group):max(phen_group) + 1].start_char
                end = tokens[min(phen_group):max(phen_group) + 1].end_char


            if min(phen_group) < context_window:
                context_start = 0
            else:
                context_start = min(phen_group) - context_window

            if max(phen_group) + context_window >= len(tokens)-1:
                context_end = len(tokens)

            else:
                context_end = max(phen_group) + context_window

            if context_start == context_end:
                context = tokens[context_start]

            else:
                context = tokens[context_start:context_end]

            found_term = dict(hpid=hpids,
                              index=[base_index + start, base_index + end],
                              matched=matched_string.text,
                              context=context.text
                              )

            if found_term not in extracted_terms:
                extracted_terms.append(found_term)

    return extracted_terms


def conflict_resolver(extracted_terms):
    """
    Pick most likely HPO ID based on context
    :param extracted_terms: list of dictionaries identified by extract_hpo_terms
    :return: list of dictionaries with resolved conflicts
    """
    model = load_model()
    if not model:
        logger.critical("Doc2vec model does not exist or could not be loaded")
        return extracted_terms

    resolved_terms = []

    for entry in extracted_terms:
        similarity_scores = []
        if len(entry['hpid']) > 1:
            for term in entry['hpid']:
                similarity_scores.append(similarity_term_to_context(term, entry['context'], model))
            idx_least_likely_term = similarity_scores.index(min(similarity_scores))
            least_likely_term = entry['hpid'][idx_least_likely_term]
            entry['hpid'].remove(least_likely_term)
        resolved_terms.append(entry)
    return resolved_terms


def hpo(text,
        correct_spelling=True,
        max_neighbors=2,
        max_length=1000000,
        context_window=8,
        resolve_conflicts=False,
        ):
    """
    extracts hpo terms from text
    :param text: text of type string
    :param correct_spelling: (True,False) attempt to correct spelling using spellcheck
    :param max_neighbors: (int) max number of phenotypic groups to attempt to search for a matching phenotype
    :param max_length: (int) max document length in characters, higher limit will require more memory
    :param context_window: (int) dimensions of context to return number of tokens in each direction
    :param resolve_conflicts: (True,False) loads big model
    :return: json of hpo terms, their indices in text and matched string
    """

    nlp.max_length = max_length

    extracted_terms = []

    chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]
    len_last_chunk = 1
    for i, chunk in enumerate(chunks):

        if correct_spelling:
            chunk = spellcheck(chunk)

        tokens = nlp(chunk)

        # Stem tokens
        stemmed_tokens = [st.stem(st.stem(x.lemma_.lower())) for x in tokens]

        # Index tokens which match stemmed phenotypes
        phenotokens, phenindeces = index_tokens(stemmed_tokens)

        # Group token indices
        groups = group_sequence(phenindeces)

        # Add leave one out groups
        groups = permute_leave_one_out(groups)

        # Find and fuse adjacent phenotype groups
        assembled_groups = assemble_groups(groups, max_distance=max_neighbors)

        phen_groups = recombine_groups(assembled_groups)

        # Extract hpo terms
        extracted_terms += find_hpo_terms(tuple(phen_groups),
                                          tuple(stemmed_tokens),
                                          tokens,
                                          base_index=i * len_last_chunk,
                                          context_window=context_window)
        len_last_chunk = len(chunk)

    if extracted_terms:
        if resolve_conflicts:
            extracted_terms = conflict_resolver(extracted_terms)

        return json.dumps(extracted_terms)
    else:
        return json.dumps([])


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

    logger.info(f"{(correct / total) * 100} percent correct, {len(wrong)} items wrong")
    return wrong
