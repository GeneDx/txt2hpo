import pandas as pd
import math


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