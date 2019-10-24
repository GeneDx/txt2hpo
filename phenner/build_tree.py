from phenopy.obo import restore
from phenopy.score import Scorer
from nltk.stem import RegexpStemmer
import re
import spacy

hpo = restore('/home/vgainullin/.phenopy/data/hpo_network.pickle')
scorer = Scorer(hpo)

st = RegexpStemmer('ing$|e$|able$|ic$|ia$|ity$', min=6)
nlp = spacy.load('en')

def build_search_tree(hpo):
    """
    Build stemmed, search tree for phenotypes / n-grams
    :param hpo: hpo object from phenopy
    :return: nested dictionary
    """

    terms = {}
    for node in hpo:
        term = hpo.node[node]['name']
        if 'synonym' in hpo.node[node]:
            synonyms = hpo.node[node]['synonym']
        else:
            synonyms = ""
        synonyms = re.findall(r'"(.*?)"', ','.join(synonyms))
        names = [term] + synonyms
        for name in names:
            tokens = nlp(name)
            tokens = [x for x in tokens if not x.is_punct]
            tokens = [x for x in tokens if not x.is_stop]
            tokens = [st.stem(x.lemma_.lower()) for x in tokens]
            for token in tokens:
                if token not in terms:
                    terms[token] = {}
                if len(tokens) not in terms[token]:
                    terms[token][len(tokens)] = {}
                terms[token][len(tokens)][' '.join(sorted(tokens))] = node
    return terms

