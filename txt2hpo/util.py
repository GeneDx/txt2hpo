import pandas as pd

import math
import obonet
import re
import sys
import subprocess
import os
import networkx as nx
from txt2hpo.config import config

# hpo_network = obonet.read_obo(obo_file)

obo_file = config.get('hpo', 'obo')

hpo_network = obonet.read_obo(obo_file)
for node_id, data in hpo_network.nodes(data=True):
    # clean synonyms
    synonyms = []
    if 'synonym' in data:
        for synonym in data['synonym']:
            synonyms.append(synonym)
        hpo_network.nodes[node_id]['synonyms'] = re.findall(r'"(.*?)"', ','.join(synonyms))

# roots for non-phenotype nodes
non_phenotypes = {
    'mortality_aging': 'HP:0040006',
    'mode_of_inheritance': 'HP:0000005',
    'clinical_modifier': 'HP:0012823',
    'frequency': 'HP:0040279',
    'clinical_course': 'HP:0031797',
}

non_phenos = {}
# remove non-phenotype branches
for name, hpo_id in non_phenotypes.items():
    if hpo_id in hpo_network.nodes:
        children = nx.ancestors(hpo_network, hpo_id)
        for hpid in [hpo_id] + list(children):
            non_phenos[hpid] = name


def group_pairs(phenotype_pairs):
    """group unique keys and combine their values"""
    unique_pairs = {}
    for k1,k2,value in phenotype_pairs:
        sorted_pair = tuple(sorted([k1,k2]))
        if sorted_pair not in unique_pairs:
            unique_pairs[sorted_pair]=[value]
        else:
            if value not in unique_pairs[sorted_pair]:
                unique_pairs[sorted_pair].append(value)
    return unique_pairs


def summarize_tuples(pairs, how='min'):
    """summarize collection of tuple with list values"""
    summarized_pairs = []
    for k,v in pairs.items():
        if how == 'min':
            summarized_value = min(v)
        elif how == 'max':
            summarized_value = max(v)
        elif how == 'mean':
            summarized_value = math.mean(v)
        summarized_pairs.append((k[0], k[1], summarized_value))
    return summarized_pairs


def df_from_tuples(tuples):
    """make pandas df from tuples"""
    tup_df = pd.DataFrame(tuples, columns=['term_a','term_b','score'])
    tup_df.index = pd.MultiIndex.from_arrays(tup_df[['term_a', 'term_b']].values.T, names=['idx1', 'idx2'])
    tup_df = tup_df[['score']]
    return tup_df


def remove_key(dict_list, key):
    """remove a key from each dict in a list of dictionaries"""
    for d in dict_list:
        if key in d:
            del d[key]
    return dict_list


def download_model(filename, user_pip_args=None):
    download_url = filename
    pip_args = ["--no-cache-dir"]
    if user_pip_args:
        pip_args.extend(user_pip_args)
    cmd = [sys.executable, "-m", "pip", "install"] + pip_args + [download_url]
    return subprocess.call(cmd, env=os.environ.copy())