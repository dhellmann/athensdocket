"""Tests for the validation code in the VTR parser.
"""

from nose.tools import assert_raises

from docket import vtr


def test_no_defendant():
    p = vtr.Parser()
    c = {'participants': [],
         'number': 1,
         }
    p.validate_case(c, 0)
    msgs = [e[-1] for e in p.errors]
    assert msgs
    assert 'No defendant' in msgs[0]
