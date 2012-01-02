
import logging

from celery.task import task
import fuzzy
from pymongo import Connection

from docket import vtr

@task
def parse_file(filename):
    """Given the name of a VTR file, parse it and load the data into the database.
    """
    log = parse_file.get_logger()
    log.info('loading from %s', filename)
    try:
        with open(filename, 'r') as f:
            parser = vtr.Parser()
            for case in parser.parse(f):
                log.info('New case: %s/%s', case['book'], case['number'])
                add_encodings_for_names.subtask().delay(case)
            errors = [ 'Parse error at %s:%s "%s" (%s)' % (filename, num, line, err)
                       for num, line, err in parser.errors
                       ]
    except (OSError, IOError) as err:
        errors = [ unicode(err) ]
    return errors

def metaphone(s, m=fuzzy.DMetaphone()):
    return m(s)[0]

ENCODERS = [
    ('soundex', fuzzy.Soundex(4)),
    ('metaphone', metaphone),
    ('nysiis', fuzzy.nysiis),
    ]
FIELDS_TO_ENCODE = [ 'first_name', 'middle_name', 'last_name' ]

@task
def add_encodings_for_names(case):
    """Add phonetic encodings for names of participants associated with a case.
    """
    log = add_encodings_for_names.get_logger()
    log.info('encoding names for %s/%s', case['book'], case['number'])
    for participant in case['participants']:
        for field in FIELDS_TO_ENCODE:
            for encoder_name, encoder in ENCODERS:
                try:
                    orig = participant[field]
                    encoded = encoder(orig) if orig else ''
                    participant['%s_%s' % (field, encoder_name)] = encoded
                except Exception as err:
                    log.error('Error encoding %s to %s for %s/%s "%s" (%s)',
                              field, encoder_name,
                              case['book'], case['number'],
                              participant[field],
                              err,
                              )
    store_case_in_database.subtask().delay(case)
    return

@task
def store_case_in_database(case):
    """Store the case in the database, updating an existing entry if found.
    """
    log = store_case_in_database.get_logger()
    case['_id'] = '%s/%s' % (case['book'], case['number'])
    log.info('storing %s', case['_id'])
    conn = Connection()
    db = conn.docket_test
    db.books.update({'_id':case['_id']},
                    case,
                    True, # upsert
                    False,
                    )
    
