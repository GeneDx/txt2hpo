
import json
import pandas as pd
import numpy as np
from txt2hpo.util import group_pairs, summarize_tuples, df_from_tuples
from txt2hpo.config import logger
from phenopy.util import half_product
from functools import reduce


def phenotype_distance(extracted_hpos):
    """
    Given the return from hpo, find the normalized distance between all terms in the document.
    This could serve as a proxy for cooccurrence.
    :param extracted_hpos: json string output of txt2hpo
    :return: list of tuples (hpo1, hpo2, distance)
    """

    # load the extracted phenotypes into a pandas DataFrame
    hpo_ids = json.loads(extracted_hpos)
    df = pd.DataFrame(hpo_ids)
    # make two rows for text offsets where more than one HPO term was identified
    df = df.explode('hpid').reset_index(drop=True)
    # location is the starting index of an HPO term in the document.
    df['location'] = df['index'].apply(min)

    # use max_idx as a normalization factor (a proxy for how long the document is)
    # TODO:
    # Maybe include the length of the text in the json object as a top-level key.
    max_idx = df['location'].max()

    # loop through the combinations and the diagonal, collect distances b/w each pair
    phenotype_pairs = []
    for hpo_pair in half_product(len(df), len(df)):
        x, y = sorted(hpo_pair, reverse=True)
        distance = abs(df.iloc[x]['location'] - df.iloc[y]['location']) / max_idx
        phenotype_pairs.append((df.iloc[x]['hpid'], df.iloc[y]['hpid'], distance))

    return phenotype_pairs


def distances(array_of_extracted_hpos, min_n_distances=2, summary_method='mean'):
    """
    Summarize array of phenotype distances generated from parsing distinct documents
    :param array_of_extracted_hpos: array of phenotype distances
    :param min_n_distances: minimum number of coocurances / distances to summarize to filter
    :param summary_method: (mean,min) how to summarize coocurances / distances
    :return: pandas dataframe
    """
    dfs = []
    if summary_method not in ['mean', 'min']:
        logger.critical(f'Summary method undefined: {summary_method} ')
        return dfs
    # process distances of each document into df
    for extracted_hpo in array_of_extracted_hpos:

        # get term-term pairwise distances for each document
        phenotype_pairs = phenotype_distance(extracted_hpo)

        # find identical pairs and combine their values
        grouped_pairs = group_pairs(phenotype_pairs)

        # get summary metric for each term pair
        summarized_pairs = summarize_tuples(grouped_pairs)

        # make a dataframe and append it to list
        tup_df = df_from_tuples(summarized_pairs)

        dfs.append(tup_df)

    # merge dataframes
    dfs_merged = reduce(lambda x, y: pd.merge(x, y, on=['idx1', 'idx2'], how="outer"), dfs)

    dfs_merged['values'] = dfs_merged.values.tolist()
    # remove nan from list of distance values
    dfs_merged['values'] = dfs_merged['values'].apply(lambda x: [v for v in x if ~np.isnan(v)])

    # keep relationships with at least 3 distance values
    dfs_merged['n'] = dfs_merged['values'].apply(len)
    dfs_merged = dfs_merged[dfs_merged['n'] > min_n_distances]

    # summarize
    if summary_method == 'mean':
        dfs_merged['mean_score'] = dfs_merged['values'].apply(np.mean)
        dfs_merged = dfs_merged[['mean_score', 'n']]

    elif summary_method == 'min':
        dfs_merged['min_score'] = dfs_merged['values'].apply(np.min)
        dfs_merged = dfs_merged[['min_score', 'n']]

    return dfs_merged.reset_index()
