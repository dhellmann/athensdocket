
from celery.task import task

from docket import vtr, encodings


@task
def parse_file(filename, db_factory, load_job_id, error_handler):
    """Parse the named VTR file and load the data into the database.
    """
    log = parse_file.get_logger()
    log.info('loading from %s', filename)
    try:
        num_cases = 0
        with open(filename, 'r') as f:
            parser = vtr.Parser()
            for case in parser.parse(f):
                log.info('New case: %s/%s', case['book'], case['number'])
                num_cases += 1
                add_encodings_for_names(case, error_handler)
                store_case_in_database(case, load_job_id, db_factory, error_handler)
            errors = ['Parse error at %s:%s "%s" (%s)' % \
                          (filename, num, line, err)
                      for num, line, err in parser.errors
                      ]
            for e in errors:
                error_handler(e)
    except (OSError, IOError) as err:
        msg = unicode(err)
        errors = [msg]
        error_handler(msg)
    return {'errors': errors,
            'num_cases': num_cases,
            }


FIELDS_TO_ENCODE = ['first_name', 'middle_name', 'last_name']


def add_encodings_for_names(case, error_handler):
    """Add phonetic encodings for names of participants associated with a case.
    """
    log = parse_file.get_logger()
    log.info('encoding names for %s/%s', case['book'], case['number'])
    for participant in case['participants']:
        for field in FIELDS_TO_ENCODE:
            for encoder_name, encoder in encodings.ENCODERS.items():
                try:
                    orig = participant[field]
                    encoded = encoder(orig) if orig else ['']
                    participant['%s_%s' % (field, encoder_name)] = encoded
                except Exception as err:
                    msg = 'Error encoding %s to %s for %s/%s "%s" (%s)' % \
                        (field, encoder_name, case['book'], case['number'],
                         participant[field], err)
                    log.error(msg)
                    error_handler(msg)
    return


def store_case_in_database(case, load_job_id, db_factory, error_handler):
    """Store the case in the database, updating an existing entry if found.
    """
    log = parse_file.get_logger()
    case['_id'] = '%s/%s' % (case['book'], case['number'])
    # associate the case record with the job for auditing
    case['load_job_id'] = load_job_id
    log.info('storing %s', case['_id'])
    db = db_factory()
    try:
        db.cases.update({'_id': case['_id']},
                        case,
                        upsert=True,
                        )
    except Exception as err:
        log.error('Could not store case %s: %s', case['_id'], err)
        error_handler(unicode(err))
    try:
        db.books.update({'book_id': case['book']},
                        {'$set': {'book_id': case['book'],
                                  'year': int(case['book'].split('/')[0]),
                                  'number': case['book'].split('/')[1],
                                  },
                         '$addToSet': {'load_jobs': load_job_id,
                                       },
                         },
                        upsert=True,
                        )
    except Exception as err:
        log.error('Could not store book %s: %s', case['book'], err)
        error_handler(unicode(err))
