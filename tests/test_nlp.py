import unittest
import time

from txt2hpo.nlp import similarity_term_to_context
from txt2hpo.data import load_model


class NLPCase(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print('%s: %.3f' % (self.id(), t))

    def test_similarity_term_to_context(self):

        model = load_model()

        context1 = 'In the sample, 14,516 children were diagnosed with , of whom 5,689 had neurological symptoms'
        context2 = 'secundum, all underwent surgical repair except for 1 individual whose defect spontaneously closed'

        # "Autistic behavior"
        term1 = 'HP:0000729'

        # "Atrial septal defect"
        term2 = 'HP:0001631'

        t_aut_c_aut = similarity_term_to_context(term1, context1, model)
        t_aut_c_chd = similarity_term_to_context(term1, context2, model)

        t_chd_c_aut = similarity_term_to_context(term2, context1, model)
        t_chd_c_chd = similarity_term_to_context(term2, context2, model)

        self.assertGreater(t_aut_c_aut, t_chd_c_aut)
        self.assertGreater(t_chd_c_chd, t_aut_c_chd)