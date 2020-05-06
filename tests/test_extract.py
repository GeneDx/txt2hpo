import unittest
import time
import json
from txt2hpo.extract import Extractor, Data, group_sequence
from txt2hpo.data import load_model
from tests.test_cases import *
from txt2hpo.util import hpo_network


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
        truth = [{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "Hypotonia"}]
        self.assertEqual(extract.hpo("Hypotonia").entries_sans_context, truth)

        # Test adding non phenotypic term
        truth = [{"hpid": ["HP:0001290"], "index": [5, 14], "matched": "hypotonia"}]
        self.assertEqual(extract.hpo("Word hypotonia").entries_sans_context, truth)

        # Test handling punctuation
        truth = [{"hpid": ["HP:0001290"], "index": [6, 15], "matched": "hypotonia"}]
        self.assertEqual(extract.hpo("Word, hypotonia").entries_sans_context, truth)

        # Test extracting a multiword phenotype
        truth = [{"hpid": ["HP:0001263"],
                             "index": [0, 19], "matched": "Developmental delay"}]
        self.assertEqual(extract.hpo("Developmental delay").entries_sans_context, truth)

        # Test extracting a multiword phenotype with reversed word order
        truth = [{"hpid": ["HP:0001263"], "index": [0, 19],
                             "matched": "Delay developmental"}]

        self.assertEqual(extract.hpo("Delay developmental").entries_sans_context, truth)

        # Test extracting a phenotype with inflectional endings
        truth = [{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "Hypotonic"}]
        self.assertEqual(extract.hpo("Hypotonic").entries_sans_context, truth)

        # Test extracting a multiword phenotype with inflectional endings and reversed order
        truth = [{"hpid": ["HP:0001263"], "index": [0, 19], "matched": "Delayed development"}]
        self.assertEqual(extract.hpo("Delayed development").entries_sans_context, truth)

        # Test extracting multiword phenotype following an unrelated phenotypic term
        truth = [{"hpid": ["HP:0000365"], "index": [6, 18], "matched": "hearing loss"}]
        self.assertEqual(extract.hpo("Delay hearing loss").entries_sans_context, truth)

        # Test extracting multiword phenotype preceding an unrelated phenotypic term
        truth = [{"hpid": ["HP:0000365"], "index": [0, 12], "matched": "Hearing loss"}]
        self.assertEqual(extract.hpo("Hearing loss following").entries_sans_context, truth)

        # Test extracting two multiword phenotype preceding interrupted by an unrelated phenotypic term
        truth = [
                            {"hpid": ["HP:0000365"], "index": [0, 12], "matched": "Hearing loss"},
                            {"hpid": ["HP:0001263"], "index": [23, 42], "matched": "developmental delay"},
                            ]
        self.assertEqual(extract.hpo("Hearing loss following developmental delay").entries_sans_context, truth)

        # Test spellchecker
        extract = Extractor(correct_spelling=True)
        truth = [{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "Hypotonic"}]

        self.assertEqual(extract.hpo("Hyptonic").entries_sans_context, truth)

        truth = []
        extract = Extractor(correct_spelling=False)
        self.assertEqual(extract.hpo("Hyptonic").entries_sans_context, truth)

        truth = [
            {"hpid": ["HP:0002757"],"index": [12, 30], "matched": "multiple fractures"},
            {"hpid": ["HP:0000938"], "index": [35, 45], "matched": "osteopenia"},
        ]

        self.assertEqual(truth, extract.hpo("Female with multiple fractures and osteopenia NA NA").entries_sans_context)

        truth = [{"hpid": ["HP:0001156"], "index": [30, 43], "matched": "brachydactyly"}]

        self.assertEqual(truth, extract.hpo("Female with fourth metacarpal brachydactyly").entries_sans_context)

        extract = Extractor(correct_spelling=False, remove_overlapping=False)
        truth = [
            {"hpid": ["HP:0000964"], "index": [10, 16], "matched": "eczema"},
            {"hpid": ["HP:0000988"], "index": [18, 27], "matched": "skin rash"},
            {"hpid": ["HP:0000988"], "index": [23, 27], "matched": "rash"},
            {"hpid": ["HP:0008070"], "index": [33, 44], "matched": "sparse hair"},
            ]
        resp = extract.hpo("Male with eczema, skin rash, and sparse hair").entries_sans_context
        self.assertEqual(truth, resp)

        # Test extracting an abbreviated phenotype
        truth = [{"hpid": ["HP:0001370"], "index": [0, 2], "matched": "RA"}]
        self.assertEqual(extract.hpo("RA").entries_sans_context, truth)

        # Test extracting multiple phenotypes
        truth = [{"hpid": ["HP:0001290"], "index": [0, 9], "matched": "Hypotonia"},
                            {"hpid": ["HP:0001263"], "index": [11, 30], "matched": "developmental delay"
                             }]
        self.assertEqual(extract.hpo("Hypotonia, developmental delay").entries_sans_context, truth)

        # Test term indexing given max length of extracted text
        extract = Extractor(correct_spelling=False, max_length=20, chunk_by="max_length")
        truth = [
            {"hpid": ["HP:0001263"], "index": [0, 19], "matched": "Developmental delay"},
            {"hpid": ["HP:0001290"], "index": [21, 30], "matched": "hypotonia"}
        ]
        self.assertEqual(extract.hpo("Developmental delay, hypotonia").entries_sans_context, truth)

    def test_stop_word_phenos(self):
        # Test extracting multiple phenotypes with max_neighbors
        extract = Extractor(correct_spelling=True, max_neighbors=3)
        truth = [{"hpid": ["HP:0001263"], "index": [0, 23], "matched": "developmental and delay"}]
        self.assertEqual(extract.hpo("developmental and delay").entries_sans_context, truth)

        extract = Extractor(correct_spelling=True, max_neighbors=1)
        truth = []
        self.assertEqual(extract.hpo("developmental and delay").entries_sans_context, truth)

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

    def test_hpo_big_text_spellcheck_on(self):
        # test parsing a page
        extract = Extractor(max_neighbors=2, remove_overlapping=False)
        self.assertEqual(extract.hpo(test_case11_text).n_entries, 12)

    def test_hpo_big_text_spellcheck_off(self):
        # test parsing a page
        extract = Extractor(max_neighbors=2, correct_spelling=False, remove_overlapping=True)
        self.assertEqual(extract.hpo(test_case11_text).n_entries, 7)

    def test_hpo_big_text_spellcheck_off_max3(self):
        # test parsing a page
        extract = Extractor(max_neighbors=3, correct_spelling=False, remove_overlapping=True)
        self.assertEqual(extract.hpo(test_case11_text).n_entries, 8)

    def test_hpo_big_text_max_neighbors(self):
        # test parsing a page
        extract = Extractor(max_neighbors=1, correct_spelling=True, remove_overlapping=False)
        hpo_max_2 = extract.hpo(test_case11_text).hpids
        extract = Extractor(max_neighbors=3, correct_spelling=True, remove_overlapping=False)
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
        extract = Extractor(correct_spelling=True)
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
                  "matched": "ASD"}]

        data = Data(entries=extracted, model=model)
        data.resolve_conflicts()
        self.assertEqual(truth, data.entries_sans_context)

        extracted = [{"hpid": ["HP:0000729", "HP:0001631"],
                  "index": [44, 47],
                  "matched": "ASD",
                  "context": "secundum, all underwent surgical repair for ASD except for 1 individual \
                  whose defect spontaneously closed"}]

        truth = [{"hpid": ["HP:0001631"],
                  "index": [44, 47],
                  "matched": "ASD"}]

        data = Data(entries=extracted, model=model)
        data.resolve_conflicts()
        self.assertEqual(truth, data.entries_sans_context)

        # Test conflict resolution if terms have identical context similarity scores

        extracted = [{"hpid": ["HP:0001631", "HP:0001631"],
                      "index": [44, 47],
                      "matched": "ASD",
                      "context": "secundum, all underwent surgical repair for ASD except for 1 individual \
                          whose defect spontaneously closed"}]

        # Expected result remove only one term
        truth = [{"hpid": ["HP:0001631"],
                  "index": [44, 47],
                  "matched": "ASD"}]

        data = Data(entries=extracted, model=model)
        data.resolve_conflicts()
        self.assertEqual(truth, data.entries_sans_context)

        # Test conflict resolution if terms have identical context similarity scores

        extracted = [{"hpid": ["HP:0001631", "HP:0001631"],
                      "index": [44, 47],
                      "matched": "ASD",
                      "context": "secundum, all underwent surgical repair for ASD except for 1 individual \
                                  whose defect spontaneously closed"}]

        # Expected result remove only one term
        truth = [{"hpid": ["HP:0001631"],
                  "index": [44, 47],
                  "matched": "ASD"}]

        data = Data(entries=extracted, model=model)
        data.resolve_conflicts()
        self.assertEqual(truth, data.entries_sans_context)

        # Test conflict resolution if 2 of 3 terms have identical context similarity scores

        extracted = [{"hpid": ["HP:0000729", "HP:0001631", "HP:0001631"],
                      "index": [44, 47],
                      "matched": "ASD",
                      "context": "secundum, all underwent surgical repair for ASD except for 1 individual \
                                          whose defect spontaneously closed"}]

        # Expected result remove only one term
        truth = [{"hpid": ["HP:0001631"],
                  "index": [44, 47],
                  "matched": "ASD"}]

        data = Data(entries=extracted, model=model)
        data.resolve_conflicts()
        self.assertEqual(truth, data.entries_sans_context)

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
        truth = [{"hpid": ["HP:0001631"], "index": [44, 47], "matched": "ASD"}]
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
        extract = Extractor(max_neighbors=2)
        truth = json.dumps([{"hpid": ["HP:0000154"],
                             "index": [16, 26],
                             "matched": "wide mouth"}])
        resp = extract.hpo("Wide gait and a wide mouth")
        self.assertEqual(truth, resp.json)

    def test_extract_without_negated(self):

        # negation should not apply if negation is part of matched string
        extract = Extractor(remove_negated=True)
        resp = extract.hpo("the patient presents with absent speech")
        self.assertEqual(resp.hpids, ['HP:0001344'])

        extract = Extractor()
        resp = extract.hpo("developmental delay and a wide mouth")
        resp.detect_negation()
        self.assertEqual(set(['HP:0000154', 'HP:0001263']), set(resp.hpids))

        resp = extract.hpo("developmental delay with no wide mouth")
        resp.detect_negation()
        resp.remove_negated()
        self.assertEqual(['HP:0001263'], resp.hpids)

        extract = Extractor(remove_negated=True)
        resp = extract.hpo("developmental delay without a wide mouth")
        self.assertEqual(['HP:0001263'], resp.hpids)

        extract = Extractor(remove_negated=True)
        resp = extract.hpo("no developmental delay, but has a wide mouth")
        self.assertEqual(['HP:0000154'], resp.hpids)

        extract = Extractor(remove_negated=True)
        resp = extract.hpo("the patient has a wide mouth but no developmental delay.")
        self.assertEqual(['HP:0000154'], resp.hpids)

        extract = Extractor(remove_negated=True)
        resp = extract.hpo("the patient does not have either a wide mouth or developmental delay.")
        self.assertEqual([], resp.hpids)

    def test_capitalization_affecting_outcome(self):
        extract = Extractor(correct_spelling=False)
        resp = extract.hpo("enlarged heart")
        self.assertEqual(resp.hpids, ['HP:0001640'])

        resp = extract.hpo(" enlarged heart")
        self.assertEqual(resp.hpids, ['HP:0001640'])

        resp = extract.hpo("Enlarged heart")
        self.assertEqual(resp.hpids, ['HP:0001640'])

        resp = extract.hpo(" Enlarged heart")
        self.assertEqual(resp.hpids, ['HP:0001640'])

        resp = extract.hpo("Male with Sotos, enlarged heart")
        self.assertEqual(resp.hpids, ['HP:0001640'])
        
        resp = extract.hpo("Myoclonus Seizures")
        self.assertEqual(set(resp.hpids), set(['HP:0002123']))

    def test_remove_overlapping(self):
        extract = Extractor(correct_spelling=False, remove_overlapping=False)
        resp = extract.hpo("Polycystic kidney disease and myoclonus seizures.")
        self.assertEqual(set(resp.hpids), set(['HP:0000113', 'HP:0000112', 'HP:0001250', 'HP:0002123','HP:0001336']))

        extract = Extractor(correct_spelling=False, remove_overlapping=True)
        resp = extract.hpo("Polycystic kidney disease and myoclonus seizures.")
        self.assertEqual(set(resp.hpids), set(['HP:0002123','HP:0000113']))

    def test_multiple_matches(self):
        extract = Extractor(correct_spelling=False, remove_overlapping=True, resolve_conflicts=True)
        resp = extract.hpo("l pre auricular ear pit.")
        self.assertEqual(resp.hpids, ['HP:0004467'])
        resp = extract.hpo("Coloboma, microphthalmia, macrocephaly, ear pit.")
        self.assertEqual(set(resp.hpids), set(['HP:0000589', 'HP:0004467', 'HP:0000568', 'HP:0000256']))

    def test_handing_term_hyphenation(self):
        extract = Extractor(correct_spelling=False, remove_overlapping=True, resolve_conflicts=True)
        hyphenated_phenos = \
            [
            (hpo_network.nodes()[x]['name'], x) for x in hpo_network.nodes() \
            if (
                    '-' in hpo_network.nodes()[x]['name'] and
                    ',' not in hpo_network.nodes()[x]['name'] and
                    '.' not in hpo_network.nodes()[x]['name']
                )

            ]
        # Phenotypes where word-order is important is a limitation of current parsing method
        known_bugs = ['HP:0000510', 'HP:0030932']
        #known_bugs = []
        long_phenos = ['HP:0011654', 'HP:0410303']
        hyphenated_phenos = [x for x in hyphenated_phenos if x[1] not in known_bugs + long_phenos]

        for test in hyphenated_phenos:
            # current version is not expected to extract very long phenotypes
            hpids = extract.hpo(test[0]).hpids
            self.assertEqual(hpids, [test[1]])
            # replace hyphens with space
            hpids = extract.hpo(test[0].replace('-', ' ')).hpids
            self.assertEqual(hpids, [test[1]])
