# -*- encoding: utf-8 -*-

from docket import encodings
from docket import tasks


def check_one_participant(participant, case):
    assert 'encoding' in participant
    assert participant['case'] == case['_id']


def test():
    errors = []
    c = {'participants': [{'first_name': u'Douglas',
                           'middle_name': u'Richard',
                           'last_name': u'Hellmann',
                           },
                          ],
         'book': 'test',
         'number': '0',
         '_id': 'case-id-goes-here',
         }
    encoded_participants = list(
        tasks.get_encoded_participants(c,
                                       error_handler=errors.append,
                                       )
        )
    actual_encodings = set(p['encoding'] for p in encoded_participants)
    assert actual_encodings == set(encodings.ENCODERS.keys())
    for p in encoded_participants:
        yield check_one_participant, p, c


def test_fields():
    assert tasks.FIELDS_TO_ENCODE


def test_encoders():
    assert encodings.ENCODERS


def test_normalize_case():
    assert encodings.normalize(u'ABC') == ['abc']


def test_normalize_punctuation():
    assert encodings.normalize(u'A.B.C.') == ['abc']
