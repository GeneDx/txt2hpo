
# Peter Norvig spell checker https://norvig.com/spell-correct.html

from txt2hpo.nlp import nlp_sans_ner
from txt2hpo.data.spellcheck_vocab import spellcheck_vocab


def P(word, N=sum(spellcheck_vocab.values())):
    "Probability of `word`."
    if word in spellcheck_vocab:
        return spellcheck_vocab[word] / N
    else:
        return 0.1/N


def correction(word):
    "Most probable spelling correction for word."
    return max(candidates(word), key=P)


def candidates(word):
    "Generate possible spelling corrections for word."
    return (known([word]) or known(edits1(word)) or known(edits2(word)) or [word])


def known(words):
    "The subset of `words` that appear in the dictionary of spellcheck_data."
    return set(w for w in words if w in spellcheck_vocab)


def edits1(word):
    "All edits that are one edit away from `word`."
    letters    = 'abcdefghijklmnopqrstuvwxyz'
    splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
    deletes    = [L + R[1:]               for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
    replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
    inserts    = [L + c + R               for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)


def edits2(word):
    "All edits that are two edits away from `word`."
    return (e2 for e1 in edits1(word) for e2 in edits1(e1))


def spellcheck(text):
    "correct spelling in a sentence"
    # clean up text from punctuation marks
    corrected_text = []
    for token in nlp_sans_ner(text):

        if token.is_stop:
            corrected_text.append(token.text_with_ws)

        elif token.is_punct:
            corrected_text.append(token.text_with_ws)

        elif len(token) < 5:
            corrected_text.append(token.text_with_ws)
        else:
            corrected_text.append(correction(token.text))
            corrected_text.append(token.whitespace_)

    return "".join(corrected_text)