import unittest
import time
import json
from txt2hpo.extract import Extractor, Data, group_sequence
from txt2hpo.data import load_model
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

        extract = Extractor(correct_spelling=False)

        # Test extracting single phenotype
        truth = [{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "Hypotonia", "context": "Hypotonia"}]
        self.assertEqual(extract.hpo("Hypotonia").entries, truth)

        # Test adding non phenotypic term
        truth = [{"hpid": ["HP:0001290"], "index": [5, 14], "matched": "hypotonia", "context": "Word hypotonia"}]
        self.assertEqual(extract.hpo("Word hypotonia").entries, truth)

        # Test handling punctuation
        truth = [{"hpid": ["HP:0001290"], "index": [6, 15], "matched": "hypotonia", "context": "Word, hypotonia"}]
        self.assertEqual(extract.hpo("Word, hypotonia").entries, truth)

        # Test extracting a multiword phenotype
        truth = [{"hpid": ["HP:0001263"],
                             "index": [0, 19], "matched": "Developmental delay",
                             "context": "Developmental delay"}]
        self.assertEqual(extract.hpo("Developmental delay").entries, truth)

        # Test extracting a multiword phenotype with reversed word order
        truth = [{"hpid": ["HP:0001263"], "index": [0, 19],
                             "matched": "Delay developmental",
                             "context": "Delay developmental"}]

        self.assertEqual(extract.hpo("Delay developmental").entries, truth)

        # Test extracting a phenotype with inflectional endings
        truth = [{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "Hypotonic", "context": "Hypotonic"}]
        self.assertEqual(extract.hpo("Hypotonic").entries, truth)

        # Test extracting a multiword phenotype with inflectional endings and reversed order
        truth = [{"hpid": ["HP:0001263"], "index": [0, 19], "matched": "Delayed development",
                             "context": "Delayed development"}]
        self.assertEqual(extract.hpo("Delayed development").entries, truth)

        # Test extracting multiword phenotype following an unrelated phenotypic term
        truth = [{"hpid": ["HP:0000365"], "index": [6, 18],
                             "matched": "hearing loss", "context":"Delay hearing loss"}]
        self.assertEqual(extract.hpo("Delay hearing loss").entries, truth)

        # Test extracting multiword phenotype preceding an unrelated phenotypic term
        truth = [{"hpid": ["HP:0000365"], "index": [0, 12],
                             "matched": "Hearing loss", "context":"Hearing loss following"}]
        self.assertEqual(extract.hpo("Hearing loss following").entries, truth)

        # Test extracting two multiword phenotype preceding interrupted by an unrelated phenotypic term
        truth = [
                            {"hpid": ["HP:0001263"], "index": [23, 42], "matched": "developmental delay",
                             "context": "Hearing loss following developmental delay"},
                            {"hpid": ["HP:0000365"], "index": [0, 12], "matched": "Hearing loss",
                             "context":"Hearing loss following developmental delay"}
                            ]
        self.assertEqual(extract.hpo("Hearing loss following developmental delay").entries, truth)

        # Test spellchecker
        extract = Extractor(correct_spelling=True)
        truth = [{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "hypotonic",
                             "context":"hypotonic"}]

        self.assertEqual(extract.hpo("hyptonic").entries, truth)

        truth = []
        extract = Extractor(correct_spelling=False)
        self.assertEqual(extract.hpo("hyptonic").entries, truth)

        truth = [{"hpid": ["HP:0000938"], "index": [35, 45], "matched": "osteopenia",
                             "context":"Female with multiple fractures and osteopenia NA NA"},
                        {"hpid": ["HP:0002757"],"index": [12, 30], "matched": "multiple fractures",
                         "context": "Female with multiple fractures and osteopenia NA NA"}]

        self.assertEqual(truth, extract.hpo("Female with multiple fractures and osteopenia NA NA").entries)

        truth = [{"hpid": ["HP:0001156"], "index": [30, 43], "matched": "brachydactyly",
                             "context": "Female with fourth metacarpal brachydactyly"}]

        self.assertEqual(truth, extract.hpo("Female with fourth metacarpal brachydactyly").entries)

        extract = Extractor(correct_spelling=False)
        truth = [{"hpid": ["HP:0000988"], "index": [23, 27], "matched": "rash"},
                            {"hpid": ["HP:0000988"], "index": [18, 27], "matched": "skin rash"},
                            {"hpid": ["HP:0008070"], "index": [33, 44], "matched": "sparse hair"},
                            {"hpid": ["HP:0000964"], "index": [10, 16], "matched": "eczema"}]

        self.assertEqual(truth, extract.hpo("Male with eczema, skin rash, and sparse hair").entries_sans_context)

        # Test extracting multiple phenotypes with max_neighbors
        extract = Extractor(correct_spelling=True, max_neighbors=3)
        truth = [{"hpid": ["HP:0001263"], "index": [0, 23], "matched": "developmental and delay",
                             "context": "developmental and delay"}]
        self.assertEqual(extract.hpo("developmental and delay").entries, truth)

        extract = Extractor(correct_spelling=True, max_neighbors=1)
        truth = []
        self.assertEqual(extract.hpo("developmental and delay").entries, truth)

        extract = Extractor(correct_spelling=False)

        # Test extracting single phenotype followed by multiword phenotype
        truth = [
                 {"hpid": ["HP:0000750"], "index": [0, 12], "matched": "Speech delay"},
                 {"hpid": ["HP:0100710"], "index": [17, 26], "matched": "impulsive"}
        ]
        self.assertEqual(extract.hpo("Speech delay and impulsive").entries_sans_context, truth)

        # Test extracting multiword phenotype followed by single phenotype
        truth = [
                 {"hpid": ["HP:0100710"], "index": [0, 9], "matched": "Impulsive"},
                 {"hpid": ["HP:0000750"], "index": [14, 26], "matched": "speech delay"}
                 ]
        self.assertEqual(extract.hpo("Impulsive and speech delay").entries_sans_context, truth)

        # Test extracting an abbreviated phenotype
        truth = [{"hpid": ["HP:0001370"], "index": [0, 2], "matched": "RA"}]
        self.assertEqual(extract.hpo("RA").entries_sans_context, truth)

        # Test extracting multiple phenotypes
        truth = [{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "Hypotonia"},
                            {"hpid": ["HP:0001263"], "index": [11, 30], "matched": "developmental delay"
                             }]
        self.assertEqual(extract.hpo("Hypotonia, developmental delay").entries_sans_context, truth)

        # Test term indexing given max length of extracted text
        extract = Extractor(correct_spelling=False, max_length=20)
        truth = [
            {"hpid": ["HP:0001263"], "index": [0, 19], "matched": "Developmental delay"},
            {"hpid": ["HP:0001290"], "index": [21, 30], "matched": "hypotonia"}
        ]
        self.assertEqual(extract.hpo("Developmental delay, hypotonia").entries_sans_context, truth)

    def test_hpo_big_text_spellcheck_on(self):
        # test parsing a page
        extract = Extractor(max_neighbors=2)
        self.assertEqual(extract.hpo(test_case11_text).n_entries, 10)

    def test_hpo_big_text_spellcheck_off(self):
        # test parsing a page
        extract = Extractor(max_neighbors=2, correct_spelling=False)
        self.assertEqual(extract.hpo(test_case11_text).n_entries, 10)

    def test_hpo_big_text_spellcheck_off_max3(self):
        # test parsing a page
        extract = Extractor(max_neighbors=3, correct_spelling=False)
        self.assertEqual(extract.hpo(test_case11_text).n_entries, 11)

    def test_hpo_big_text_max_neighbors(self):
        # test parsing a page
        extract = Extractor(max_neighbors=2, correct_spelling=True)
        hpo_max_2 = extract.hpo(test_case11_text).hpids
        extract = Extractor(max_neighbors=3, correct_spelling=True)
        hpo_max_3 = extract.hpo(test_case11_text).hpids

        self.assertNotEqual(hpo_max_2, hpo_max_3)

    def test_iteration_over_chunks(self):
        # test performing multiple extractions in a row
        sentences = ['Developmental delay', 'Hypotonia']
        extract = Extractor(correct_spelling=False)
        for sentence in sentences:
            self.assertNotEqual(extract.hpo(sentence).n_entries, 0)
        sentences = ['Hypotonia', 'Developmental delay']
        for sentence in sentences:
            self.assertNotEqual(extract.hpo(sentence).n_entries, 0)
        hpo = Extractor(correct_spelling=True)
        sentences = ['Developmental delay', 'Hypotonia']
        for sentence in sentences:
            self.assertNotEqual(extract.hpo(sentence).n_entries, 0)
        sentences = ['Hypotonia', 'Developmental delay']
        for sentence in sentences:
            self.assertNotEqual(extract.hpo(sentence).n_entries, 0)
        sentences = ['Developmental delay', 'Hypotonia']
        for sentence in sentences:
            self.assertNotEqual(extract.hpo(sentence).n_entries, 0)
        sentences = ['Hypotonia', 'Developmental delay']
        for sentence in sentences:
            self.assertNotEqual(extract.hpo(sentence).n_entries, 0)

    def test_conflict_resolver(self):

        model = load_model()

        extracted = [{"hpid": ["HP:0000729", "HP:0001631"],
                    "index": [50, 53],
                    "matched": "ASD",
                    "context": "the sample, 14,16 children were diagnosed with ASD, of whom 5689 had neurological and"}]
        truth = [{"hpid": ["HP:0000729"],
                  "index": [50, 53],
                  "matched": "ASD",
                  "context": "the sample, 14,16 children were diagnosed with ASD, of whom 5689 had neurological and"}]

        data = Data(entries=extracted, model=model)
        data.resolve_conflicts()
        self.assertEqual(truth, data.entries)

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

        data = Data(entries=extracted, model=model)
        data.resolve_conflicts()
        self.assertEqual(truth, data.entries)

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

        data = Data(entries=extracted, model=model)
        data.resolve_conflicts()
        self.assertEqual(truth, data.entries)

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

        data = Data(entries=extracted, model=model)
        data.resolve_conflicts()
        self.assertEqual(truth, data.entries)

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

        data = Data(entries=extracted, model=model)
        data.resolve_conflicts()
        self.assertEqual(truth, data.entries)

    def test_custom_synonyms(self):
        # test adding custom synonyms
        custom_syn = {"HP:0001263": ['DD', 'GDD'], "HP:0000729": ['ASD', 'PDD']}

        extract = Extractor(custom_synonyms=custom_syn)
        truth = [{"hpid": ["HP:0001263"], "index": [0, 3], "matched": "GDD"},
                            {"hpid": ["HP:0001263"], "index": [4, 6], "matched": "DD"}]
        self.assertEqual(extract.hpo("GDD DD").entries_sans_context, truth)

    def test_extract_ambiguous(self):
        # test resolver works
        extract = Extractor(resolve_conflicts=True)
        truth = [{"hpid": ["HP:0001631"], "index": [44, 47], "matched": "asd"}]
        test1 = extract.hpo("secundum, all underwent surgical repair for ASD except for 1 individual whose defect spontaneously closed")
        self.assertEqual(truth, test1.entries_sans_context)

    def test_conflict_instantiate(self):
        # Test that reinstantiation does not affect results
        extract = Extractor(resolve_conflicts=True)
        self.assertEqual(extract.resolve_conflicts, True)
        res = extract.hpo("ASD")
        self.assertEqual(len(res.entries[0]['hpid']), 1)

        extract = Extractor(resolve_conflicts=False)
        self.assertEqual(extract.resolve_conflicts, False)
        res = extract.hpo("ASD")
        self.assertEqual(len(res.entries[0]['hpid']), 2)

        extract = Extractor(resolve_conflicts=True)
        self.assertEqual(extract.resolve_conflicts, True)
        res = extract.hpo("ASD")
        self.assertEqual(len(res.entries[0]['hpid']), 1)

    def test_extract_from_repeated_context(self):
        extract = Extractor()
        truth = [{"hpid": ["HP:0000154"], "index": [16, 26], "matched": "wide mouth"}]
        resp = extract.hpo("Wide gait and a wide mouth")
        self.assertEqual(truth, resp.entries_sans_context)

    def test_extract_json_property(self):
        extract = Extractor()
        truth = json.dumps([{"hpid": ["HP:0000154"],
                             "index": [16, 26],
                             "matched": "wide mouth",
                             "context": "Wide gait and a wide mouth"}])
        resp = extract.hpo("Wide gait and a wide mouth")
        self.assertEqual(truth, resp.json)
