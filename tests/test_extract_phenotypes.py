import os
import unittest
import pandas as pd
from phenner.extract_phenotypes import extract_hpos


class ExtractPhenotypesTestCase(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.parent_dir = os.path.dirname(os.path.realpath(__file__))
        cls.test_file = os.path.join(cls.parent_dir, 'data/CR_comparison_summary.HPOids.txt')
        cls.test_cases_df = pd.read_csv(cls.test_file, sep='tsv')

    def test_extract_hpos(self):

        # Test extracting single phenotype
        truth = [{'hpid': ['HP:0001290'], 'index': [0], 'matched': 'hypotonia'}]
        self.assertEqual(extract_hpos('hypotonia'), truth)

        # Test adding non phenotypic term
        truth = [{'hpid': ['HP:0001290'], 'index': [1], 'matched': 'hypotonia'}]
        self.assertEqual(extract_hpos('word hypotonia'), truth)

        # Test handling punctuation
        truth = [{'hpid': ['HP:0001290'], 'index': [2], 'matched': 'hypotonia'}]
        self.assertEqual(extract_hpos('word, hypotonia'), truth)

        # Test extracting a multiword phenotype
        truth = [{'hpid': ['HP:0001263'], 'index': [0, 1], 'matched': 'developmental delay'}]
        self.assertEqual(extract_hpos('developmental delay'), truth)

        # Test extracting a multiword phenotype with reversed word order
        truth = [{'hpid': ['HP:0001263'], 'index': [0, 1], 'matched': 'delay developmental'}]
        self.assertEqual(extract_hpos('delay developmental'), truth)

        # Test extracting a phenotype with inflectional endings
        truth = [{'hpid': ['HP:0001290'], 'index': [0], 'matched': 'hypotonic'}]
        self.assertEqual(extract_hpos('hypotonic'), truth)

        # Test extracting a multiword phenotype with inflectional endings and reversed order
        truth = [{'hpid': ['HP:0001263'], 'index': [0, 1], 'matched': 'delayed development'}]
        self.assertEqual(extract_hpos('delayed development'), truth)

        # Test extracting multiple phenotypes
        truth = [{'hpid': ['HP:0001290'], 'index': [0], 'matched': 'hypotonia'},
                 {'hpid': ['HP:0001263'], 'index': [2, 3], 'matched': 'developmental delay'}]
        self.assertEqual(extract_hpos('hypotonia, developmental delay'), truth)

        # Test spellchecker
        truth = [{'hpid': ['HP:0001290'], 'index': [0], 'matched': 'hypotonic'}]
        self.assertEqual(extract_hpos('hyptonic', correct_spelling=True), truth)

        truth = []
        self.assertEqual(extract_hpos('hyptonic', correct_spelling=False), truth)

        # Test extracting multiple phenotypes with max_neighbors
        truth = [{'hpid': ['HP:0001263'], 'index': [0, 2], 'matched': 'developmental and delay'}]
        self.assertEqual(extract_hpos('developmental and delay', max_neighbors=2), truth)
        truth = []
        self.assertEqual(extract_hpos('developmental and delay', max_neighbors=1), truth)
