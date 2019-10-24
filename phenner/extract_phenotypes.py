import spacy
from phenner import build_tree
from nltk.stem import RegexpStemmer

nlp = spacy.load('en')

st = RegexpStemmer('ing$|e$|able$|ic$|ia$|ity$', min=6)
max_search = 5
terms = build_tree()

def search_hp(tokens):
    results = []
    if not tokens:
        return results
    token = tokens[0]
    for i in range(len(tokens) + 1):
        if not token in terms:
            return results
        else:
            if not i in terms[token]:
                continue
            else:
                try_term = ' '.join(sorted(tokens[:i]))
                if try_term in terms[token][i].keys():
                    results.append(terms[token][i][try_term])
    return results


def extract_hpos(text):
    hpo = []
    for i, word in enumerate(text.split()):

        try:
            subset = text.split()[i:max_search + i]
        except:
            subset = text.split()[i:]
        subset = [x for x in subset]
        subset = nlp(" ".join(subset))

        search_space = [st.stem(x.lemma_.lower()) for x in subset if not x.is_stop and not x.is_punct]

        hpo += search_hp(search_space)
    return hpo