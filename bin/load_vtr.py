#!/usr/bin/env python
"""CLI app to load VTR files into the database.
"""

import argparse
import logging
import os
import sys

from pymongo import Connection

sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))
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

    if args.reset_db:
        log.info('Resetting the database...')
        conn = Connection()
        db = getattr(conn, args.database)
        db.drop_collection('books')
        conn.disconnect()
        del conn

    task_results = [
        (name,
         tasks.parse_file.delay(
                os.path.abspath(name),
                tasks.add_encodings_for_names.subtask(
                    kwargs={
                        'callback': tasks.store_case_in_database.subtask(
                            kwargs={'dbname':args.database}),
                        }
                    )
                )
         )
        for name in args.filenames
        ]
    for name, tr in task_results:
        log.info('waiting for %s', name)
        errors = tr.get()
        for e in errors:
            log.error('%s: %s', name, e)
        else:
            log.info('finished processing %s', name)

if __name__ == '__main__':
    main()
