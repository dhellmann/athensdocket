#!/usr/bin/env python
"""CLI app to show details of a particular job that ran to load data into the database
"""

import argparse
import json
import os
import sys

from pymongo import Connection

sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))


def main():
    parser = argparse.ArgumentParser(
        description='CLI app to list the load jobs in the docket database',
        )
    parser.add_argument('-q', dest='verbosity', action='store_const',
                        const=[],
                        help='Quiet mode',
                        )
    parser.add_argument('--db', dest='database', action='store',
                        default='docket',
                        help='Database name',
                        )
    parser.add_argument('job', action='store',
                        help='Job ID',
                        )
    args = parser.parse_args()

    conn = Connection()
    db = getattr(conn, args.database)

    results = db.jobs.find({'_id': args.job})
    for job in results:
        job['start'] = job['start'].isoformat()
        job['errors'] = list(db.errors.find({'job_id': args.job}))
        print json.dumps(job,
                         sort_keys=True,
                         indent=2,
                         default=unicode,
                         )
    return 0

if __name__ == '__main__':
    sys.exit(main())
