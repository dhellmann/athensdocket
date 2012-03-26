"""Tests for the code in the VTR parser that sets defaults for the case fields.
"""

import datetime

from docket import vtr


def test_year_from_book():
    p = vtr.Parser()
    c = {'participants': [],
         'number': 1,
         'book':'1901/1',
         }
    p.prepare_case(c, 0)
    assert c['year'] == 1901


def test_year_from_arrest_date():
    p = vtr.Parser()
    c = {'participants': [],
         'number': 1,
         'book':'1901/1',
         'arrest_date':datetime.datetime(1902, 1, 1, 1, 1)
         }
    p.prepare_case(c, 0)
    assert c['year'] == 1902
