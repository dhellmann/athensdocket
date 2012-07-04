import codecs

from celery.task import task

from docket import vtr, encodings


@task
def parse_file(filename, db_factory, load_job_id, error_handler):
    """Parse the named VTR file and load the data into the database.
    """
    db = db_factory()
    log = parse_file.get_logger()
    log.info('loading from %s', filename)
    try:
        num_cases = 0
        with codecs.open(filename, 'r', encoding='utf-8') as f:
            parser = vtr.Parser()
            for case in parser.parse(f):
                log.info('New case: %s/%s', case['book'], case['number'])
                num_cases += 1

                # Store the book
                try:
                    db.books.update({'_id': case['book']},
                                    {'$set': {'year': int(case['book'].split('/')[0]),
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

                # Store the case
                case['_id'] = '%s/%s' % (case['book'], case['number'])
                # associate the case record with the job for auditing
                case['load_job_id'] = load_job_id
                # pick a "date" for the case
                case['date'] = case.get('hearing_date') or case.get('arrest_date')
                try:
                    db.cases.update({'_id': case['_id']},
                                    case,
                                    upsert=True,
                                    )
                except Exception as err:
                    log.error('Could not store case %s: %s', case['_id'], err)
                    error_handler(unicode(err))

                # Add participant info

                # index for upsert
                for p in get_encoded_participants(case, error_handler):
                    #log.info('new participant: %r', p)
                    p['case_id'] = case['_id']
                    p['case_number'] = case['number']
                    p['date'] = case['date']
                    try:
                        db.participants.update(
                            {'case': case['_id'],
                             'encoding': p['encoding'],
                             'full_name': p['full_name'],
                             'role': p['role'],
                             },
                            p,
                            upsert=True,
                            )
                    except Exception as err:
                        log.error('Could not store participant %s for case %s: %s',
                                  p['_id'], case['_id'], err)
                        error_handler(unicode(err))

            # Handle errors that did not result in new case records.
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


def get_encoded_participants(case, error_handler):
    """Return participant documents with encoded names.
    """
    log = parse_file.get_logger()
    for participant in case['participants']:
        for encoder_name, encoder in encodings.ENCODERS.items():
            result = {'encoding': encoder_name,
                      'case': case['_id'],
                      }
            result.update(participant)
            for field in FIELDS_TO_ENCODE:
                try:
                    orig = participant[field]
                    encoded = encoder(orig) if orig else ['']
                    result[field] = encoded
                except Exception as err:
                    msg = 'Error encoding %s to %s for %s/%s "%s" (%s)' % \
                        (field, encoder_name, case['book'], case['number'],
                         participant[field], err)
                    log.error(msg)
                    error_handler(msg)
            yield result
