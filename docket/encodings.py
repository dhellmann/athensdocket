import fuzzy


def metaphone(s, e=fuzzy.DMetaphone()):
    return e(s)


def soundex(s, e=fuzzy.Soundex(4)):
    # Return a list to be like metaphone
    return [e(s)]


def nysiis(s, e=fuzzy.nysiis):
    # Return a list to be like metaphone
    return [e(s)]


def normalize(s):
    # Return a list to be like metaphone
    return [s.lower()]


ENCODERS = {
    'soundex': soundex,
    'metaphone': metaphone,
    'nysiis': nysiis,
    'normalized': normalize,
    }
