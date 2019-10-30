import unittest

from phenner.extract_phenotypes import extract_hpos, group_sequence


class ExtractPhenotypesTestCase(unittest.TestCase):

    def test_group_sequence(self):
        truth = [[0, 1], [3]]
        self.assertEqual(group_sequence([0, 1, 3]), truth)

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

        # Test extracting single phenotype followed by multiword phenotype
        truth = [{'hpid': ['HP:0100710'], 'index': [3], 'matched': 'impulsive'},
                 {'hpid': ['HP:0000750'], 'index': [0, 1], 'matched': 'speech delay'}]
        self.assertEqual(extract_hpos("speech delay and impulsive"), truth)

        # Test extracting multiword phenotype followed by single phenotype
        truth = [{'hpid': ['HP:0100710'], 'index': [0], 'matched': 'impulsive'},
                 {'hpid': ['HP:0000750'], 'index': [2, 3], 'matched': 'speech delay'}]
        self.assertEqual(extract_hpos("impulsive and speech delay"), truth)
