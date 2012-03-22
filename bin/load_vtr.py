#!/usr/bin/env python
"""CLI app to load VTR files into the database.
"""

import argparse
import datetime
import logging
import os
import sys
import uuid

from pymongo import Connection

sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))
from docket import db
from docket import tasks


def main():
    parser = argparse.ArgumentParser(
        description='CLI app to load VTR files into the docket database',
        )
    parser.add_argument('filenames', nargs='+')
    parser.add_argument('-v', dest='verbosity', default=[None],
                        action='append_const', const=None,
                        help='Increase verbosity',
                        )
    parser.add_argument('-q', dest='verbosity', action='store_const',
                        const=[],
                        help='Quiet mode',
                        )
    parser.add_argument('--db', dest='database', action='store',
                        default='docket',
                        help='Database name',
                        )
    parser.add_argument('--reset-db', dest='reset_db', action='store_true',
                        default=False,
                        help='Reset (drop) the database before loading data',
                        )
    args = parser.parse_args()

    verbosity = len(args.verbosity)
    if verbosity < 0:
        verbosity = 0
    if verbosity > 2:
        verbosity = 2
    level = {0: logging.WARNING,
             1: logging.INFO,
             2: logging.DEBUG,
             }[verbosity]
    logging.basicConfig(level=level,
                        format='%(levelname)-8s %(name)s %(message)s',
                        )
    log = logging.getLogger('vtr_loader')

    conn = Connection()
    database = getattr(conn, args.database)

    if args.reset_db:
        log.info('Resetting the database...')
        database.drop_collection('books')

    job_id = unicode(uuid.uuid4())
    job_start = datetime.datetime.utcnow()

    log.info('Starting job %s', job_id)

    # Get full paths to the input filenames
    filenames = [os.path.abspath(f)
                 for f in args.filenames
                 ]

    # Record the beginning of the database
    database.jobs.insert({'_id': job_id,
                          'start': job_start,
                          'filenames': filenames,
                          })

    # Start the tasks to parse the input files
    task_results = []
    db_factory = db.DBFactory(args.database)
    for name in filenames:

        error_handler = db.ErrorHandler(db_factory, job_id, name)

        store_task = tasks.store_case_in_database.subtask(
            kwargs={'db_factory': db_factory,
                    'error_handler': error_handler,
                    'load_job_id': job_id,
                    },
            )

        encode_task = tasks.add_encodings_for_names.subtask(
            kwargs={'db_factory': db_factory,
                    'error_handler': error_handler,
                    'callback': store_task,
                    },
            )

        parse_task = tasks.parse_file.delay(
            filename=os.path.abspath(name),
            db_factory=db_factory,
            error_handler=error_handler,
            callback=encode_task,
            )

        task_results.append((name, parse_task))

    for name, tr in task_results:
        log.debug('waiting for %s', name)
        file_results = tr.get()
        log.info('%s: processed %d cases', name, file_results['num_cases'])
        for e in file_results['errors']:
            log.error('%s: %s', name, e)

if __name__ == '__main__':
    main()
