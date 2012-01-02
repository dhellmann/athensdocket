
import logging

from celery.task import task

from docket import vtr

@task
def parse_file(filename):
    log = parse_file.get_logger()
    log.info('loading from %s', filename)
    try:
        with open(filename, 'r') as f:
            parser = vtr.Parser()
            for record in parser.parse(f):
                log.info('New case: %s/%s', record['book'], record['number'])
            errors = [ 'Parse error at %s:%s "%s" (%s)' % (filename, num, line, err)
                       for num, line, err in parser.errors
                       ]
    except (OSError, IOError) as err:
        errors = [ unicode(err) ]
    return errors
