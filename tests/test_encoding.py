from mock import Mock

from docket import encodings
from docket import tasks


def check_one(field_name, encoding_name, case):
    expected_field = '%s_%s' % (field_name, encoding_name)
    assert expected_field in case['participants'][0]
    assert case['participants'][0][expected_field]


def test():
    errors = []
    c = {'participants': [{'first_name':'Dougas',
                           'middle_name':'Richard',
                           'last_name':'Hellmann',
                           },
                          ],
         'book': 'test',
         'number': '0',
         }
    tasks.add_encodings_for_names(c,
                                  db_factory=Mock,
                                  error_handler=errors.append,
                                  )
    for field in tasks.FIELDS_TO_ENCODE:
        for encoder_name, encoder in encodings.ENCODERS.items():
            yield check_one, field, encoder_name, c


def test_fields():
    assert tasks.FIELDS_TO_ENCODE


def test_encoders():
    assert encodings.ENCODERS
