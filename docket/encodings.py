import string

import fuzzy


def metaphone(s, e=fuzzy.DMetaphone()):
    return e(s)


def soundex(s, e=fuzzy.Soundex(4)):
    # Return a list to be like metaphone
    return [e(s)]


def nysiis(s, e=fuzzy.nysiis):
    # Return a list to be like metaphone
    return [e(s)]


def normalize(s,
              trans=string.maketrans(string.lowercase, string.lowercase),
              delete=string.punctuation,
              ):
    # Return a list to be like metaphone
    return [s.lower().translate(trans, delete)]


ENCODERS = {
    'soundex': soundex,
    'metaphone': metaphone,
    'nysiis': nysiis,
    'normalized': normalize,
    }
