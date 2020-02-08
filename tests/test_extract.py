import unittest
import json
import time

from txt2hpo.extract import hpo, group_sequence, conflict_resolver
from tests.test_cases import *
from txt2hpo.data import load_model

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

        # Test extracting an abbreviated phenotype
        truth = json.dumps([{"hpid": ["HP:0001370"], "index": [0, 2], "matched": "RA"}])
        self.assertEqual(hpo("RA"), truth)

        # Test extracting single phenotype
        truth = json.dumps([{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "Hypotonia", "context": "Hypotonia"}])
        self.assertEqual(hpo("Hypotonia", return_context=True, correct_spelling=False), truth)

        # Test adding non phenotypic term
        truth = json.dumps([{"hpid": ["HP:0001290"], "index": [5, 14], "matched": "hypotonia", "context": "Word hypotonia"}])
        self.assertEqual(hpo("Word hypotonia", return_context=True), truth)

        # Test handling punctuation
        truth = json.dumps([{"hpid": ["HP:0001290"], "index": [6, 15], "matched": "hypotonia", "context": "Word, hypotonia"}])
        self.assertEqual(hpo("Word, hypotonia", return_context=True), truth)

        # Test extracting a multiword phenotype
        truth = json.dumps([{"hpid": ["HP:0001263"],
                             "index": [0, 19], "matched": "Developmental delay",
                             "context": "Developmental delay"}])
        self.assertEqual(hpo("Developmental delay", return_context=True, correct_spelling=False), truth)

        # Test extracting a multiword phenotype with reversed word order
        truth = json.dumps([{"hpid": ["HP:0001263"], "index": [0, 19],
                             "matched": "Delay developmental",
                             "context": "Delay developmental"}])

        self.assertEqual(hpo("Delay developmental", return_context=True, correct_spelling=False), truth)

        # Test extracting a phenotype with inflectional endings
        truth = json.dumps([{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "Hypotonic", "context": "Hypotonic"}])
        self.assertEqual(hpo("Hypotonic", return_context=True, correct_spelling=False), truth)

        # Test extracting a multiword phenotype with inflectional endings and reversed order
        truth = json.dumps([{"hpid": ["HP:0001263"], "index": [0, 19], "matched": "Delayed development",
                             "context": "Delayed development"}])
        self.assertEqual(hpo("Delayed development", return_context=True, correct_spelling=False), truth)

        # Test extracting multiword phenotype following an unrelated phenotypic term
        truth = json.dumps([{"hpid": ["HP:0000365"], "index": [6, 18],
                             "matched": "hearing loss", "context":"Delay hearing loss"}])
        self.assertEqual(hpo("Delay hearing loss", return_context=True, correct_spelling=False), truth)

        # Test extracting multiword phenotype preceding an unrelated phenotypic term
        truth = json.dumps([{"hpid": ["HP:0000365"], "index": [0, 12],
                             "matched": "Hearing loss", "context":"Hearing loss following"}])
        self.assertEqual(hpo("Hearing loss following", return_context=True, correct_spelling=False), truth)

        # Test extracting two multiword phenotype preceding interrupted by an unrelated phenotypic term
        truth = json.dumps([
                            {"hpid": ["HP:0001263"], "index": [23, 42], "matched": "developmental delay",
                             "context": "Hearing loss following developmental delay"},
                            {"hpid": ["HP:0000365"], "index": [0, 12], "matched": "Hearing loss",
                             "context":"Hearing loss following developmental delay"}
                            ])
        self.assertEqual(hpo("Hearing loss following developmental delay", return_context=True, correct_spelling=False), truth)

        # Test extracting multiple phenotypes
        truth = json.dumps([{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "Hypotonia"},
                 {"hpid": ["HP:0001263"], "index": [11, 30], "matched": "developmental delay"
                  }])
        self.assertEqual(hpo("Hypotonia, developmental delay",correct_spelling=False), truth)

        # Test spellchecker
        truth = json.dumps([{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "hypotonic",
                             "context":"hypotonic"}])
        self.assertEqual(hpo("hyptonic", correct_spelling=True, return_context=True), truth)

        truth = json.dumps([])
        self.assertEqual(hpo("hyptonic", correct_spelling=False, return_context=True), truth)

        truth = json.dumps([{"hpid": ["HP:0000938"], "index": [35, 45], "matched": "osteopenia",
                             "context":"Female with multiple fractures and osteopenia NA NA"},
                        {"hpid": ["HP:0002757"],"index": [12, 30], "matched": "multiple fractures",
                         "context": "Female with multiple fractures and osteopenia NA NA"}])

        self.assertEqual(truth, hpo("Female with multiple fractures and osteopenia NA NA",
                                    correct_spelling=False,
                                    return_context=True))

        truth = json.dumps([{"hpid": ["HP:0001156"], "index": [30, 43], "matched": "brachydactyly",
                             "context": "female with fourth metacarpal brachydactyly"}])

        self.assertEqual(truth, hpo("Female with fourth metacarpal brachydactyly", return_context=True))

        truth = json.dumps([{"hpid": ["HP:0000988"], "index": [23, 27], "matched": "rash"},
                            {"hpid": ["HP:0000988"],"index": [18, 27], "matched": "skin rash"},
                            {"hpid": ["HP:0008070"], "index": [33, 44], "matched": "sparse hair"},
                            {"hpid": ["HP:0000964"], "index": [10, 16], "matched": "eczema"}])
        self.assertEqual(truth, hpo("Male with eczema, skin rash, and sparse hair"))
        self.assertEqual(truth, hpo("Male with eczema, skin rash, and sparse hair",correct_spelling=False))

        # Test extracting multiple phenotypes with max_neighbors
        truth = json.dumps([{"hpid": ["HP:0001263"], "index": [0, 23], "matched": "developmental and delay",
                             "context": "developmental and delay"}])
        self.assertEqual(hpo("developmental and delay", max_neighbors=3, return_context=True), truth)
        truth = json.dumps([])
        self.assertEqual(hpo("developmental and delay", max_neighbors=1, return_context=True), truth)

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
        self.assertEqual(len(json.loads(hpo(test_case11_text, max_neighbors=2))), 9)

    def test_hpo_big_text_spellcheck_off(self):
        # test parsing a page
        self.assertEqual(len(json.loads(hpo(test_case11_text, max_neighbors=2, correct_spelling=False))), 9)

    def test_hpo_big_text_spellcheck_off_max3(self):
        # test parsing a page
        self.assertEqual(len(json.loads(hpo(test_case11_text, max_neighbors=3, correct_spelling=False))), 10)

    def test_hpo_big_text_max_neighbors(self):
        # test parsing a page
        hpo_max_2 = json.loads(hpo(test_case11_text, max_neighbors=2))
        hpo_max_3 = json.loads(hpo(test_case11_text, max_neighbors=3))

        self.assertNotEqual(hpo_max_2, hpo_max_3)

    def test_iteration_over_chunks(self):
        # test performing multiple extractions in a row
        sentences = ['Developmental delay', 'Hypotonia']
        for sentence in sentences:
            result = json.loads(hpo(sentence, correct_spelling=False))
            self.assertNotEqual(len(result), 0)
        sentences = ['Hypotonia', 'Developmental delay']

        for sentence in sentences:
            result = json.loads(hpo(sentence, correct_spelling=False))
            self.assertNotEqual(len(result), 0)

        sentences = ['Developmental delay', 'Hypotonia']
        for sentence in sentences:
            result = json.loads(hpo(sentence, correct_spelling=True))
            self.assertNotEqual(len(result), 0)
        sentences = ['Hypotonia', 'Developmental delay']

        for sentence in sentences:
            result = json.loads(hpo(sentence, correct_spelling=True))
            self.assertNotEqual(len(result), 0)

        sentences = ['Developmental delay', 'Hyptonia']
        for sentence in sentences:
            result = json.loads(hpo(sentence, correct_spelling=True))
            self.assertNotEqual(len(result), 0)
        sentences = ['Hyptonia', 'Developmental delay']

        for sentence in sentences:
            result = json.loads(hpo(sentence, correct_spelling=True))
            self.assertNotEqual(len(result), 0)

    def test_conflict_resolver(self):

        context_model = load_model()
        extracted = [{"hpid": ["HP:0000729", "HP:0001631"],
                    "index": [50, 53],
                    "matched": "ASD",
                    "context": "the sample, 14,16 children were diagnosed with ASD, of whom 5689 had neurological and"}]

        truth = [{"hpid": ["HP:0000729"],
                    "index": [50, 53],
                    "matched": "ASD",
                    "context": "the sample, 14,16 children were diagnosed with ASD, of whom 5689 had neurological and"}]

        self.assertEqual(truth, conflict_resolver(extracted, context_model))

        extracted = [{"hpid": ["HP:0000729", "HP:0001631"],
                  "index": [44, 47],
                  "matched": "ASD",
                  "context": "secundum, all underwent surgical repair for ASD except for 1 individual \
                  whose defect spontaneously closed"}]

        truth = [{"hpid": ["HP:0001631"],
                  "index": [44, 47],
                  "matched": "ASD",
                  "context": "secundum, all underwent surgical repair for ASD except for 1 individual \
                  whose defect spontaneously closed"}]

        self.assertEqual(truth, conflict_resolver(extracted, context_model))

        # Test conflict resolution if terms have identical context similarity scores

        extracted = [{"hpid": ["HP:0001631", "HP:0001631"],
                      "index": [44, 47],
                      "matched": "ASD",
                      "context": "secundum, all underwent surgical repair for ASD except for 1 individual \
                          whose defect spontaneously closed"}]

        # Expected result remove only one term
        truth = [{"hpid": ["HP:0001631"],
                  "index": [44, 47],
                  "matched": "ASD",
                  "context": "secundum, all underwent surgical repair for ASD except for 1 individual \
                          whose defect spontaneously closed"}]

        self.assertEqual(truth, conflict_resolver(extracted, context_model))

        # Test conflict resolution if terms have identical context similarity scores

        extracted = [{"hpid": ["HP:0001631", "HP:0001631"],
                      "index": [44, 47],
                      "matched": "ASD",
                      "context": "secundum, all underwent surgical repair for ASD except for 1 individual \
                                  whose defect spontaneously closed"}]

        # Expected result remove only one term
        truth = [{"hpid": ["HP:0001631"],
                  "index": [44, 47],
                  "matched": "ASD",
                  "context": "secundum, all underwent surgical repair for ASD except for 1 individual \
                                  whose defect spontaneously closed"}]

        self.assertEqual(truth, conflict_resolver(extracted, context_model))

        # Test conflict resolution if 2 of 3 terms have identical context similarity scores

        extracted = [{"hpid": ["HP:0000729", "HP:0001631", "HP:0001631"],
                      "index": [44, 47],
                      "matched": "ASD",
                      "context": "secundum, all underwent surgical repair for ASD except for 1 individual \
                                          whose defect spontaneously closed"}]

        # Expected result remove only one term
        truth = [{"hpid": ["HP:0001631"],
                  "index": [44, 47],
                  "matched": "ASD",
                  "context": "secundum, all underwent surgical repair for ASD except for 1 individual \
                                          whose defect spontaneously closed"}]

        self.assertEqual(truth, conflict_resolver(extracted, context_model))
