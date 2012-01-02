
from docket import tasks

def check_one(field_name, encoding_name, case):
    expected_field = '%s_%s' % (field_name, encoding_name)
    assert expected_field in case['participants'][0]
    assert case['participants'][0][expected_field]

def test():
    c = { 'participants':[{'first_name':'Dougas',
                           'middle_name':'Richard',
                           'last_name':'Hellmann',
                           },
                          ],
          'book':'test',
          'number':'0',
          }
    tasks.add_encodings_for_names(c)
    for field in tasks.FIELDS_TO_ENCODE:
        for encoder_name, encoder in tasks.ENCODERS:
            yield check_one, field, encoder_name, c

def test_fields():
    assert tasks.FIELDS_TO_ENCODE

def test_encoders():
    assert tasks.ENCODERS
    
