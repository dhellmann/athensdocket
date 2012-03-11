
from celery.task import task, subtask
import fuzzy
from pymongo import Connection

from docket import vtr


@task
def parse_file(filename, callback=None):
    """Parse the named VTR file and load the data into the database.
    """
    log = parse_file.get_logger()
    log.info('loading from %s', filename)
    try:
        with open(filename, 'r') as f:
            parser = vtr.Parser()
            for case in parser.parse(f):
                log.info('New case: %s/%s', case['book'], case['number'])
                if callback:
                    subtask(callback).delay(case)
            errors = ['Parse error at %s:%s "%s" (%s)' % \
                          (filename, num, line, err)
                      for num, line, err in parser.errors
                      ]
    except (OSError, IOError) as err:
        errors = [unicode(err)]
    return errors


def metaphone(s, e=fuzzy.DMetaphone()):
    return e(s)


def soundex(s, e=fuzzy.Soundex(4)):
    # Return a list to be like metaphone
    return [e(s)]


def nysiis(s, e=fuzzy.nysiis):
    # Return a list to be like metaphone
    return [e(s)]


ENCODERS = [
    ('soundex', soundex),
    ('metaphone', metaphone),
    ('nysiis', nysiis),
    ]
FIELDS_TO_ENCODE = ['first_name', 'middle_name', 'last_name']


@task
def add_encodings_for_names(case, callback=None):
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
    if callback:
        subtask(callback).delay(case)
    return


@task
def store_case_in_database(case, dbname):
    """Store the case in the database, updating an existing entry if found.
    """
    log = store_case_in_database.get_logger()
    case['_id'] = '%s/%s' % (case['book'], case['number'])
    log.info('storing %s', case['_id'])
    conn = Connection()
    db = getattr(conn, dbname)
    db.books.update({'_id': case['_id']},
                    case,
                    True,  # upsert
                    False,
                    )
