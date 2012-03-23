#!/usr/bin/env python
"""CLI app to load VTR files into the database.
"""

import argparse
import datetime
import logging
import os
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
    parser.add_argument('-s', '--start', dest='start_date', action='store',
                        default=None,
                        help='Start date for cases (inclusive) as YYYY-MM-DD',
                        )
    parser.add_argument('-S', '--stop', dest='stop_date', action='store',
                        default=None,
                        help='Stop date for cases (inclusive) as YYYY-MM-DD',
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
        key = 'participants.first_name_%s' % args.encoding
        query[key] = encoder(args.first)
    if args.middle:
        key = 'participants.middle_name_%s' % args.encoding
        query[key] = encoder(args.middle)
    if args.last:
        key = 'participants.last_name_%s' % args.encoding
        query[key] = encoder(args.last)
    if args.start_date:
        start = datetime.datetime.strptime(args.start_date, '%Y-%m-%d')
        ad = query.setdefault('arrest_date', {})
        ad['$gte'] = start
    if args.stop_date:
        stop = datetime.datetime.strptime(args.stop_date, '%Y-%m-%d')
        ad = query.setdefault('arrest_date', {})
        ad['$lte'] = stop

    log.debug('query=%r', query)

    if not query:
        log.error('Provide at least one search parameter')
        return 1

    conn = Connection()
    db = getattr(conn, args.database)
    results = db.cases.find(query)

    n = 0
    for case in results.sort([('_id', 1)]):
        print case['_id']
        print ' %s' % case['arrest_date'].date()
        for p in case['participants']:
            print ' %(full_name)s (%(role)s)' % p
        print
        n += 1
    log.debug('Found %d results', n)
    return 0

if __name__ == '__main__':
    sys.exit(main())
