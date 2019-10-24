import pickle

from nltk.stem.snowball import SnowballStemmer

stemmer = SnowballStemmer("english")

import spacy

from nltk.stem import RegexpStemmer


nlp = spacy.load('en')

with open("hpo_parsed_tree.pkl", "rb") as fh:
    terms = pickle.load(fh)

st = RegexpStemmer('ing$|e$|able$|ic$|ia$|ity$', min=6)
max_search = 5


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


test = "Patient abnormality body height with ectopic kidney abnormality of the bladder and abnormal scrotum."


def extract_hpos(text):
    hpo = []
    for i, word in enumerate(text.split()):
        # print(i)
        try:
            subset = text.split()[i:max_search + i]
        except:
            subset = text.split()[i:]
        subset = [x for x in subset]
        subset = nlp(" ".join(subset))
        # print(subset)
        search_space = [st.stem(x.lemma_.lower()) for x in subset if not x.is_stop and not x.is_punct]
        # print(search_space)
        hpo += search_hp(search_space)
    return hpo