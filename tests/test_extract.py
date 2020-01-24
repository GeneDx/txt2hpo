import unittest
import json
import time

from txt2hpo.extract import hpo, group_sequence
from tests.test_cases import *

class ExtractPhenotypesTestCase(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print('%s: %.3f' % (self.id(), t))

    def test_group_sequence(self):
        truth = [[0, 1], [3]]
        self.assertEqual(group_sequence([0, 1, 3]), truth)

    def test_hpo(self):

        # Test extracting single phenotype
        truth = json.dumps([{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "hypotonia"}])
        self.assertEqual(hpo("hypotonia"), truth)

        # Test adding non phenotypic term
        truth = json.dumps([{"hpid": ["HP:0001290"], "index": [5, 14], "matched": "hypotonia"}])
        self.assertEqual(hpo("word hypotonia"), truth)

        # Test handling punctuation
        truth = json.dumps([{"hpid": ["HP:0001290"], "index": [6, 15], "matched": "hypotonia"}])
        self.assertEqual(hpo("word, hypotonia"), truth)

        # Test extracting a multiword phenotype
        truth = json.dumps([{"hpid": ["HP:0001263"], "index": [0, 19], "matched": "developmental delay"}])
        self.assertEqual(hpo("developmental delay"), truth)

        # Test extracting a multiword phenotype with reversed word order
        truth = json.dumps([{"hpid": ["HP:0001263"], "index": [0, 19], "matched": "delay developmental"}])
        self.assertEqual(hpo("delay developmental"), truth)

        # Test extracting a phenotype with inflectional endings
        truth = json.dumps([{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "hypotonic"}])
        self.assertEqual(hpo("hypotonic"), truth)

        # Test extracting a multiword phenotype with inflectional endings and reversed order
        truth = json.dumps([{"hpid": ["HP:0001263"], "index": [0, 19], "matched": "delayed development"}])
        self.assertEqual(hpo("delayed development"), truth)

        # Test extracting multiword phenotype following an unrelated phenotypic term
        truth = json.dumps([{"hpid": ["HP:0000365"], "index": [6, 18], "matched": "hearing loss"}])
        self.assertEqual(hpo("delay Hearing loss"), truth)

        # Test extracting multiword phenotype preceding an unrelated phenotypic term
        truth = json.dumps([{"hpid": ["HP:0000365"], "index": [0, 12], "matched": "hearing loss"}])
        self.assertEqual(hpo("Hearing loss following"), truth)

        # Test extracting two multiword phenotype preceding interrupted by an unrelated phenotypic term
        truth = json.dumps([
                            {"hpid": ["HP:0001263"], "index": [23, 42], "matched": "developmental delay"},
                            {"hpid": ["HP:0000365"], "index": [0, 12], "matched": "hearing loss"}
                            ])
        self.assertEqual(hpo("Hearing loss following developmental delay"), truth)

        # Test extracting multiple phenotypes
        truth = json.dumps([{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "hypotonia"},
                 {"hpid": ["HP:0001263"], "index": [11, 30], "matched": "developmental delay"}])
        self.assertEqual(hpo("hypotonia, developmental delay"), truth)

        # Test spellchecker
        truth = json.dumps([{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "hypotonic"}])
        self.assertEqual(hpo("hyptonic", correct_spelling=True), truth)

        truth = json.dumps([])
        self.assertEqual(hpo("hyptonic", correct_spelling=False), truth)

        # Test extracting multiple phenotypes with max_neighbors
        truth = json.dumps([{"hpid": ["HP:0001263"], "index": [0, 23], "matched": "developmental and delay"}])
        self.assertEqual(hpo("developmental and delay", max_neighbors=3), truth)
        truth = json.dumps([])
        self.assertEqual(hpo("developmental and delay", max_neighbors=1), truth)

        # Test extracting single phenotype followed by multiword phenotype
        truth = json.dumps([
                 {"hpid": ["HP:0000750"], "index": [0, 12], "matched": "speech delay"},
                 {"hpid": ["HP:0100710"], "index": [17, 26], "matched": "impulsive"}
        ])
        self.assertEqual(hpo("speech delay and impulsive"), truth)

        # Test extracting multiword phenotype followed by single phenotype
        truth = json.dumps([
                 {"hpid": ["HP:0100710"], "index": [0, 9], "matched": "impulsive"},
                 {"hpid": ["HP:0000750"], "index": [14, 26], "matched": "speech delay"}
                 ])
        self.assertEqual(hpo("impulsive and speech delay"), truth)

        # Test term indexing given max length of extracted text

        truth = json.dumps([
                {"hpid": ["HP:0001263"], "index": [0, 19], "matched": "developmental delay"},
                {"hpid": ["HP:0001290"], "index": [21, 30], "matched": "hypotonia"}
                            ])
        self.assertEqual(hpo("developmental delay, hypotonia", max_length=20), truth)

    def test_hpo_big_text_spellcheck_on(self):
        # test parsing a page
        self.assertEqual(len(json.loads(hpo(test_case11_text, max_neighbors=2))), 8)

    def test_hpo_big_text_spellcheck_off(self):
        # test parsing a page
        self.assertEqual(len(json.loads(hpo(test_case11_text, max_neighbors=2, correct_spelling=False))), 8)

    def test_hpo_big_text_spellcheck_off_max3(self):
        # test parsing a page
        self.assertEqual(len(json.loads(hpo(test_case11_text, max_neighbors=3, correct_spelling=False))), 9)

    def test_hpo_big_text_max_neighbors(self):
        # test parsing a page
        hpo_max_2 = json.loads(hpo(test_case11_text, max_neighbors=2))
        hpo_max_3 = json.loads(hpo(test_case11_text, max_neighbors=3))

        self.assertNotEqual(hpo_max_2, hpo_max_3)

