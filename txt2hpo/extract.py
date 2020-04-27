import json
import numpy as np
from itertools import combinations, chain
import spacy
import re

from txt2hpo.build_tree import update_progress, hpo_network
from txt2hpo.config import logger
from txt2hpo.spellcheck import spellcheck
from txt2hpo.nlp import nlp_model, nlp_sans_ner, similarity_term_to_context
from txt2hpo.nlp import st
from txt2hpo.data import load_model
from txt2hpo.build_tree import search_tree, build_search_tree
from txt2hpo.util import remove_key


class Data(object):
    def __init__(self, entries=None, model=None, negation_model=None):
        if not entries:
            self.entries = []
        else:
            self.entries = entries
        self.model = model
        self.negation_model = negation_model

    def add(self,entry):
        self.entries += entry

    def remove(self, item):
        self.entries.remove(item)

    def remove_tagged(self, tag, state=True):
        to_remove = [entry for entry in self.entries if entry[tag] is state]
        for element in to_remove:
            self.remove(element)

    def detect_negation(self):
        for entry in self.entries:
            entry['negated_tokens'] = ' '.join([e.text for e in self.negation_model(entry['context']).ents if e._.negex])
            entry['negated'] = [t.text for t in nlp_sans_ner(entry['negated_tokens'])]
            if isinstance(entry['matched_tokens'], (spacy.tokens.doc.Doc, spacy.tokens.span.Span)):
                entry['matched_words'] = [t.text for t in entry['matched_tokens']]
            elif isinstance(entry['matched_tokens'], spacy.tokens.token.Token):
                entry['matched_words'] = [entry['matched_tokens'].text]
            else:
                entry['matched_words'] = []
            entry['is_negated'] = True if set(entry['negated']).intersection(set(entry['matched_words'])) else False

    def remove_negated(self):
        self.detect_negation()
        self.remove_tagged('is_negated')

    def remove_overlapping(self):
        self._mark_overlapping()
        self.remove_tagged('is_longest', False)

    def _mark_overlapping(self):
        """
        Keep only term with widest span from a list of entries
        :return: Modify self.entries
        """
        range_dict = {}
        for i, rec in enumerate(self.entries.copy()):
            new_set = set(range(rec['index'][0], rec['index'][1]))
            overlapping = [x for x in new_set if x in range_dict]
            if overlapping:
                prev_size = range_dict[overlapping[0]][0]
                if len(new_set) > prev_size:
                    for idx in new_set:
                        range_dict[idx] = (len(new_set), i)
            else:
                for idx in new_set:
                    range_dict[idx] = (len(new_set), i)

        unique_elements = set([x[1] for x in range_dict.values()])

        for i, rec in enumerate(self.entries.copy()):
            if i in unique_elements:
                rec['is_longest'] = True
            else:
                rec['is_longest'] = False
            self.entries[i] = rec

    def resolve_conflicts(self):
        """
        Pick most likely HPO ID based on context
        :param extracted_terms: list of dictionaries identified by extract_hpo_terms
        :return: list of dictionaries with resolved conflicts
        """
        if not self.model:
            logger.critical("Doc2vec model does not exist or could not be loaded")

        resolved_terms = []
        for entry in self.entries:
            similarity_scores = []
            if len(entry['hpid']) > 1:
                for term in entry['hpid']:
                    similarity_scores.append(similarity_term_to_context(term, entry['context'], self.model))

                # reduce matches until only one term left
                for i in range(len(similarity_scores) - 1):
                    idx_least_likely_term = similarity_scores.index(min(similarity_scores))
                    least_likely_term = entry['hpid'][idx_least_likely_term]
                    entry['hpid'].remove(least_likely_term)

            resolved_terms.append(entry)
        self.entries = resolved_terms

    @property
    def hpids(self):
        return list(set(np.array([x['hpid'] for x in self.entries]).flatten()))

    @property
    def json(self):
        result = self.entries_sans_context.copy()
        return json.dumps(result)

    @property
    def contents(self):
        return self.entries

    @property
    def entries_sans_context(self):
        result = self.entries.copy()
        result = sorted(result, key=lambda i: i['index'][0], reverse=False)
        result = remove_key(result, 'context')
        result = remove_key(result, 'matched_tokens')
        result = remove_key(result, 'is_longest')
        return result

    @property
    def n_entries(self):
        return len(self.entries)


class Extractor:

    """ Converts text to HPO annotated JSON object

    Args:
        correct_spelling: (True,False) attempt to correct spelling using spellcheck
        max_neighbors: (int) max number of phenotypic groups to attempt to search for a matching phenotype
        max_length: (int) max document length in characters, higher limit will require more memory
        context_window: (int) dimensions of context to return number of tokens in each direction
        resolve_conflicts: (True,False) loads big model
        custom_synonyms: (dict) dictionary of additional synonyms to map

    """

    def __init__(self, correct_spelling=True,
                 resolve_conflicts=True,
                 remove_negated=False,
                 remove_overlapping=True,
                 max_neighbors=3,
                 max_length=1000000,
                 context_window=8,
                 model=None,
                 custom_synonyms=None,
                 negation_language="en",
                 chunk_by='phrase'
                 ):

        self.correct_spelling = correct_spelling
        self.resolve_conflicts = resolve_conflicts
        self.remove_negated = remove_negated
        self.remove_overlapping = remove_overlapping
        self.max_neighbors = max_neighbors
        self.max_length = max_length
        self.context_window = context_window
        self.negation_model = nlp_model(negation_language=negation_language)
        self.chunk_by = chunk_by
        if custom_synonyms:
            self.search_tree = build_search_tree(custom_synonyms=custom_synonyms)
        else:
            self.search_tree = search_tree
        if model is None:
            self.model = load_model()

    def hpo(self, text):
        """
        extracts hpo terms from text
        :param text: text of type string
        :return: Data object
        """

        nlp_sans_ner.max_length = self.max_length

        extracted_terms = Data(model=self.model, negation_model=self.negation_model)

        len_last_chunk = 0

        if self.chunk_by == "max_length":

            chunks = [text[i:i + self.max_length] for i in range(0, len(text), self.max_length)]
        elif self.chunk_by == "phrase":
            chunks = re.split(";|,|\n|\r|\.", text)

        for i, chunk in enumerate(chunks):

            if self.correct_spelling:
                chunk = spellcheck(chunk)

            tokens = nlp_sans_ner(chunk)

            # Stem tokens
            stemmed_tokens = [st.stem(st.stem(x.lemma_.lower())) for x in tokens]

            # Index tokens which match stemmed phenotypes
            phenotokens, phenindeces = self.index_tokens(stemmed_tokens)

            # Group token indices
            groups = group_sequence(phenindeces)

            # Add leave one out groups
            groups = permute_leave_one_out(groups)

            # Find and fuse adjacent phenotype groups
            assembled_groups = assemble_groups(groups, max_distance=self.max_neighbors)

            phen_groups = recombine_groups(assembled_groups)

            # Extract hpo terms keep track of chunked coordinates, split character len=1

            extracted_terms.add(self.find_hpo_terms(tuple(phen_groups),
                                              tuple(stemmed_tokens),
                                              tokens,
                                              base_index=len_last_chunk,
                                              ))
            if self.chunk_by == 'phrase':
                len_last_chunk += len(chunk) + 1
            elif self.chunk_by == 'max_length':
                len_last_chunk += len(chunk)

        if extracted_terms:
            if self.resolve_conflicts is True:
                extracted_terms.resolve_conflicts()
            else:
                pass

        if self.remove_negated:
            extracted_terms.remove_negated()

        if self.remove_overlapping:
            extracted_terms.remove_overlapping()

        return extracted_terms

    def find_hpo_terms(self, phen_groups, stemmed_tokens, tokens, base_index):
        """Match hpo terms from stemmed tree to indexed groups in text"""
        extracted_terms = []

        # remove stop words and punctuation from group of phenotypes
        stop_punct_mask = [x.i for x in tokens if x.is_stop or x.is_punct]
        cln_phen_groups = []
        for grp in phen_groups:
            cand_grp = [x for x in grp if not x in stop_punct_mask]
            if cand_grp:
                cln_phen_groups.append(cand_grp)

        for phen_group in cln_phen_groups:

            # if there is only one phenotype in a group
            if len(phen_group) == 1:
                phen_group_string = stemmed_tokens[phen_group[0]]
                phen_group_strings = [phen_group_string]

            # if multiple phenotypes, get all words between
            else:
                phen_start = min(phen_group)
                phen_stop = max(phen_group) + 1
                phen_group_tokens = tokens[phen_start:phen_stop]
                phen_group_tokens_minus_trash = [x for x in phen_group_tokens if not x.is_stop and not x.is_punct]
                phen_group_tokens_minus_trash_idx = [x.i for x in phen_group_tokens_minus_trash]
                phen_group_strings = [stemmed_tokens[x] for x in phen_group_tokens_minus_trash_idx] #phen_group_tokens_minus_trash_idx

            try_term_key = ' '.join(sorted(phen_group_strings))

            # attempt to extract hpo terms from tree based on root, length of phrase and key
            try:
                # copy matching hpids, because we may need to delete conflicting terms without affecting this obj
                hpids = self.search_tree[phen_group_strings[0]][len(phen_group_strings)][try_term_key].copy()

            except (KeyError, IndexError):
                hpids = []

            # if found any hpids, append to extracted
            if hpids:
                # extract span of just matching phenotype tokens
                matching_tokens_index = [x.i for x in tokens if x.i in phen_group]

                if len(matching_tokens_index) == 1:
                    matched_tokens = tokens[matching_tokens_index[0]]
                    matched_string = matched_tokens.text
                    start = matched_tokens.idx
                    end = start + len(matched_string)

                else:
                    matched_tokens = tokens[min(matching_tokens_index):max(matching_tokens_index) + 1]
                    matched_string = matched_tokens.text
                    start = matched_tokens.start_char
                    end = matched_tokens.end_char

                if min(matching_tokens_index) < self.context_window:
                    context_start = 0
                else:
                    context_start = min(matching_tokens_index) - self.context_window

                if max(matching_tokens_index) + self.context_window >= len(tokens) - 1:
                    context_end = len(tokens)

                else:
                    context_end = max(matching_tokens_index) + self.context_window

                if context_start == context_end:
                    context = tokens[context_start]

                else:
                    context = tokens[context_start:context_end]

                found_term = dict(hpid=hpids,
                                  index=[base_index + start, base_index + end],
                                  matched=matched_string,
                                  context=context.text,
                                  matched_tokens=matched_tokens,
                                  )

                if found_term not in extracted_terms:
                    extracted_terms.append(found_term)

        return extracted_terms

    def index_tokens(self, stemmed_tokens):
        """index phenotype tokens by matching each stem against root of search tree"""
        phenotokens = []
        phenindices = []
        for i, token in enumerate(stemmed_tokens):
            if token in self.search_tree:
                phenotokens.append(token)
                phenindices.append(i)

        return phenotokens, phenindices


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


def self_evaluation(correct_spelling=False, resolve_conflicts=False):
    total = 0
    correct = 0
    wrong = []

    print("")
    logger.info('Running self evaluation, this may take a few minutes \n')
    i = 0
    n_nodes = len(hpo_network.nodes)
    ext = Extractor(correct_spelling=correct_spelling, remove_overlapping=True, resolve_conflicts=True)
    for node in hpo_network:
        total += 1
        term = hpo_network.nodes[node]['name']
        hpids = []
        extracted = ext.hpo(term).hpids
        if str(node) in extracted:
            correct += 1
        else:
            wrong.append(dict(
                actual=node,
                actual_name=term,
                extracted=hpids,
                extracted_name=[hpo_network.nodes[x]['name'] for x in hpids],
            ))

        i += 1
        progress = i / n_nodes
        update_progress(progress)

    logger.info('Done \n')

    logger.info(f"{(correct / total) * 100} percent correct, {len(wrong)} items wrong")
    return wrong
