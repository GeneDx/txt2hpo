import unittest

import tests.test_cases as tc
from txt2hpo.summarize import phenotype_distance, distances


class ExtractPhenotypesTestCase(unittest.TestCase):

    def test_phenotype_distance(self):
        "[{'hpid': ['HP:0001290'], 'index': [895, 904], 'matched': 'hypotonia'}," \
        "{'hpid': ['HP:0000218'], 'index': [3184, 3195], 'matched': 'high palate'}]"
        truth = [('HP:0000218', 'HP:0001290', abs(3184 - 895) / 3184)]
        result = phenotype_distance(tc.test_case0)
        result = [x for x in result if x[0] != x[1]]
        self.assertEqual(result, truth)

        """[{"hpid": ["HP:0001290"], "index": [895, 904], "matched": "hypotonia"}, 
         {"hpid": ["HP:0002014"], "index": [1597, 1605], "matched": "diarrhea"}, 
         {"hpid": ["HP:0000218"], "index": [3184, 3195], "matched": "high palate"}]"""

        truth = [('HP:0002014', 'HP:0001290', 0.22047738693467336),
                 ('HP:0000218', 'HP:0001290', 0.7189070351758794),
                 ('HP:0000218', 'HP:0002014', 0.498429648241206)]
        result = phenotype_distance(tc.test_case1)
        result = [x for x in result if x[0] != x[1]]
        self.assertEqual(result, truth)

        # Hypotonia is seen twice
        """[{"hpid": ["HP:0001290"], "index": [895, 904], "matched": "hypotonia"},
              {"hpid": ["HP:0001290"], "index": [1095, 1104], "matched": "hypotonia"},
              {"hpid": ["HP:0002014"], "index": [1597, 1605], "matched": "diarrhea"}, 
             {"hpid": ["HP:0000218"], "index": [3184, 3195], "matched": "high palate"}]"""

        # Multiple unique entries for repeated term
        truth = [('HP:0002014', 'HP:0001290', 0.22047738693467336),
                 ('HP:0000218', 'HP:0001290', 0.7189070351758794),
                 ('HP:0002014', 'HP:0001290', 0.15766331658291458),
                 ('HP:0000218', 'HP:0001290', 0.6560929648241206),
                 ('HP:0000218', 'HP:0002014', 0.498429648241206)]
        result = phenotype_distance(tc.test_case2)
        result = [x for x in result if x[0] != x[1]]
        self.assertEqual(result, truth)

    def test_distances(self):
        test_cases = [tc.test_case0, tc.test_case1, tc.test_case2]
        truth = [{'idx1': 'HP:0001290', 'idx2': 'HP:0001290', 'mean_score': 0.0, 'n': 3 },
                 {'idx1': 'HP:0000218', 'idx2': 'HP:0001290', 'mean_score': 0.6979690117252931, 'n': 3},
                 {'idx1': 'HP:0000218', 'idx2': 'HP:0000218', 'mean_score': 0.0, 'n': 3},
                 {'idx1': 'HP:0001290', 'idx2': 'HP:0002014', 'mean_score': 0.18907035175879397, 'n': 2},
                 {'idx1': 'HP:0002014', 'idx2': 'HP:0002014', 'mean_score': 0.0, 'n': 2},
                 {'idx1': 'HP:0000218', 'idx2': 'HP:0002014', 'mean_score': 0.498429648241206, 'n': 2}]
        result = distances(test_cases, min_n_distances=1).to_dict("records")
        self.assertEqual(result, truth)

        truth = [{'idx1': 'HP:0001290', 'idx2': 'HP:0001290', 'mean_score': 0.0, 'n': 3},
                 {'idx1': 'HP:0000218', 'idx2': 'HP:0001290', 'mean_score': 0.6979690117252931, 'n': 3},
                 {'idx1': 'HP:0000218', 'idx2': 'HP:0000218', 'mean_score': 0.0, 'n': 3}]

        result = distances(test_cases, min_n_distances=2).to_dict("records")
        self.assertEqual(result, truth)