#!/usr/bin/env python
"""CLI app to load VTR files into the database.
"""

import argparse
import logging
import os
import pprint
import sys

from pymongo import Connection

sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))
from docket.encodings import ENCODERS


def main():
    parser = argparse.ArgumentParser(
        description='CLI app to search cases in the docket database',
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
    parser.add_argument('-f', '--first', dest='first', action='store',
                        default=None,
                        help='First name',
                        )
    parser.add_argument('-m', '--middle', dest='middle', action='store',
                        default=None,
                        help='Middle name',
                        )
    parser.add_argument('-l', '--last', dest='last', action='store',
                        default=None,
                        help='Last name',
                        )
    parser.add_argument('-e', '--encoding', dest='encoding', action='store',
                        default='normalized',
                        choices=sorted(ENCODERS.keys()),
                        help='Which form of the name should be searched?',
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

    # Build the search query
    query = {}
    encoder = ENCODERS[args.encoding]
    if args.first:
        query['participants.first_name_%s' % args.encoding] = encoder(args.first)
    if args.middle:
        query['participants.middle_name_%s' % args.encoding] = encoder(args.middle)
    if args.last:
        query['participants.last_name_%s' % args.encoding] = encoder(args.last)

    if not query:
        log.error('Provide at least one of --first, --middle, or --last')
        return 1
    fields = {'load_job_id': 1,
              'first_name': 1,
              'middle_name': 1,
              'last_name': 1,
              }
    fields.update(query)

    conn = Connection()
    db = getattr(conn, args.database)

    log.debug(query)

    results = db.cases.find(query)
    for case in results:
        pprint.pprint(case)
        print
    return 0

if __name__ == '__main__':
    sys.exit(main())
