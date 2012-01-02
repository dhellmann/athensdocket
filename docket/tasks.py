
import logging

from celery.task import task
import fuzzy

from docket import vtr

@task
def parse_file(filename):
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

ENCODERS = [
    ('soundex', fuzzy.Soundex(4)),
    ('metaphone', fuzzy.DMetaphone()),
    ('nysiis', fuzzy.nysiis),
    ]
FIELDS_TO_ENCODE = [ 'first_name', 'middle_name', 'last_name' ]

@task
def add_encodings_for_names(case):
    log = add_encodings_for_names.get_logger()
    log.info('encoding names for %s/%s', case['book'], case['number'])
    for participant in case['participants']:
        for field in FIELDS_TO_ENCODE:
            for encoder_name, encoder in ENCODERS:
                try:
                    participant['%s_%s' % (field, encoder_name)] = encoder(participant[field])
                except Exception as err:
                    log.error('Error encoding %s to %s for %s/%s "%s" (%s)',
                              field, encoder_name,
                              case['book'], case['number'],
                              participant[field],
                              err,
                              )
    return
