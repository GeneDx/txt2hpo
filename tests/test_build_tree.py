import unittest
import time

from txt2hpo.build_tree import build_search_tree


class BuildTreeTestCase(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print('%s: %.3f' % (self.id(), t))

    def test_build_search_tree(self):
        custom_synonyms = {"HP:0001263": ['DD', 'GDD']}
        search_tree = build_search_tree(custom_synonyms)
        self.assertEqual(search_tree['dd'], {1: {'dd': ['HP:0001263']}})
        self.assertEqual(search_tree['gdd'], {1: {'gdd': ['HP:0001263']}})
