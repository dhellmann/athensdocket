#!/usr/bin/env python
"""CLI app to list the jobs that have run to load data into the database.
"""

import argparse
import logging
import os
import sys

from pymongo import Connection

sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))


def main():
    parser = argparse.ArgumentParser(
        description='CLI app to list the load jobs in the docket database',
        )
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
    log = logging.getLogger('list_jobs')

    conn = Connection()
    db = getattr(conn, args.database)

    results = db.jobs.find({}).sort([('start', -1)])
    n = 0
    for job in results:
        print job['start'], job['_id']
        n += 1
    log.debug('Found %d results', n)
    return 0

if __name__ == '__main__':
    sys.exit(main())
