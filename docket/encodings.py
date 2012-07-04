# -*- encoding: utf-8 -*-

import fuzzy


def metaphone(s, e=fuzzy.DMetaphone()):
    return e(s)


def soundex(s, e=fuzzy.Soundex(4)):
    # Return a list to be like metaphone
    return [e(s)]


def nysiis(s, e=fuzzy.nysiis):
    # Return a list to be like metaphone
    return [e(s)]


CHARS_TO_DELETE = dict((ord(c), None)
                       for c in u'!"#%\'()*+,-./:;<=>?@[\]^_`{|}~'
                       )


def normalize(s):
    # Return a list to be like metaphone
    return [s.lower().translate(CHARS_TO_DELETE)]


def exact(s):
    # Return a list to be like metaphone
    return [s]


ENCODERS = {
    'exact': exact,
    'soundex': soundex,
    'metaphone': metaphone,
    'nysiis': nysiis,
    'normalized': normalize,
    }
