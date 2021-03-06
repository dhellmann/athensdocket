#!/usr/bin/env python
"""CLI app to load VTR files into the database.
"""

import argparse
import csv
import logging

from pymongo import Connection


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
    log = logging.getLogger('violation_loader')

    if args.reset_db:
        log.info('Resetting the database...')
        conn = Connection()
        db = getattr(conn, args.database)
        db.drop_collection('violation_codes')
        conn.disconnect()
        del conn

    conn = Connection()
    db = getattr(conn, args.database)
    violation_codes = db.violation_codes

    for name in args.filenames:
        with open(name, 'r') as f:
            log.info('loading codes from %s', name)
            for code in csv.DictReader(f):
                log.debug('code %(_id)s: %(summary)s', code)
                try:
                    code['code'] = int(code['_id'])
                except (TypeError, ValueError):
                    code['code'] = code['_id']
                violation_codes.update(
                    {'_id': code['_id']},
                    code,
                    True,  # upsert
                    False,
                    )

if __name__ == '__main__':
    main()
