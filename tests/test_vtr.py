
from docket import vtr
import pyparsing

from nose.tools import assert_raises

import datetime

def test_book():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1900/1
c 1
""".splitlines()))
    assert len(cases) == 1
    assert cases[0]['book'] == '1900/1'

def test_multiple_cases():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1900/1
c 1
c 2
""".splitlines()))
    assert len(cases) == 2

def test_dates():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ad 30 Mar 1903
hd 01 Apr 1903
""".splitlines()))
    case = cases[0]
    assert case['arrest_date'] == datetime.date(1903, 3, 30)
    assert case['hearing_date'] == datetime.date(1903, 4, 1)

def test_defendant_simple():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
d Charley Thomas
""".splitlines()))
    case = cases[0]
    assert len(case['participants']) == 1
    part = case['participants'][0]
    assert part['role'] == 'defendant'
    assert part['full_name'] == 'Charley Thomas'
    assert part['first_name'] == 'Charley'
    assert part['middle_name'] == ''
    assert part['last_name'] == 'Thomas'

def test_defendant_middle_initial():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
d Charley M. Thomas
""".splitlines()))
    case = cases[0]
    assert len(case['participants']) == 1
    part = case['participants'][0]
    assert part['role'] == 'defendant'
    assert part['full_name'] == 'Charley M. Thomas'
    assert part['first_name'] == 'Charley'
    assert part['middle_name'] == 'M.'
    assert part['last_name'] == 'Thomas'

def test_defendant_two_middle_names():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
d Charley MidA MidB Thomas
""".splitlines()))
    case = cases[0]
    assert len(case['participants']) == 1
    part = case['participants'][0]
    assert part['role'] == 'defendant'
    assert part['full_name'] == 'Charley MidA MidB Thomas'
    assert part['first_name'] == 'Charley'
    assert part['middle_name'] == 'MidA MidB'
    assert part['last_name'] == 'Thomas'

def test_defendant_note():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 75
c 824
d William Griffith (alias William Bolton)
""".splitlines()))
    case = cases[0]
    assert len(case['participants']) == 1
    part = case['participants'][0]
    assert part['role'] == 'defendant'
    assert part['full_name'] == 'William Griffith'
    assert part['first_name'] == 'William'
    assert part['middle_name'] == ''
    assert part['last_name'] == 'Griffith'
    assert part['note'] == 'alias William Bolton'

def test_witness_title():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 147
c 103
w C. A. Lambert title=Mrs.
""".splitlines()))
    case = cases[0]
    assert len(case['participants']) == 1
    part = case['participants'][0]
    assert part['role'] == 'witness'
    assert part['full_name'] == 'C. A. Lambert'
    assert part['first_name'] == 'C.'
    assert part['middle_name'] == 'A.'
    assert part['last_name'] == 'Lambert'
    assert part.get('title') == 'Mrs.'

def test_defense_witness_title():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 147
c 103
dw C. A. Lambert title=Mrs.
""".splitlines()))
    case = cases[0]
    assert len(case['participants']) == 1
    part = case['participants'][0]
    assert part['role'] == 'defense witness'
    assert part['full_name'] == 'C. A. Lambert'
    assert part['first_name'] == 'C.'
    assert part['middle_name'] == 'A.'
    assert part['last_name'] == 'Lambert'
    assert part.get('title') == 'Mrs.'

def test_defendant_suffix():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 119
c 21
d Jerry Brown suffix=Jr.
""".splitlines()))
    case = cases[0]
    assert len(case['participants']) == 1
    part = case['participants'][0]
    assert part['role'] == 'defendant'
    assert part['full_name'] == 'Jerry Brown'
    assert part['first_name'] == 'Jerry'
    assert part['middle_name'] == ''
    assert part['last_name'] == 'Brown'
    assert part.get('suffix') == 'Jr.'

def test_defendant_vehicle():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 119
c 21
d Jerry Brown suffix=Jr.
dv abc 123
""".splitlines()))
    case = cases[0]
    assert case['vehicle'] == 'abc 123'

def test_violation():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 119
c 21
v 123
""".splitlines()))
    case = cases[0]
    assert case['violation'] == '123'

def test_violation_note():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 119
c 21
v 123 (some additional info)
""".splitlines()))
    case = cases[0]
    assert case['violation'] == '123'
    assert case['violation_note'] == 'some additional info'

def test_location():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 174
l College & River Streets
""".splitlines()))
    case = cases[0]
    assert case['location'] == 'College & River Streets'

def test_arresting_officer():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ao Hamilton
""".splitlines()))
    case = cases[0]
    assert len(case['participants']) == 1
    part = case['participants'][0]
    assert part['role'] == 'arresting officer'
    assert part['full_name'] == 'Hamilton'
    assert part['first_name'] == ''
    assert part['middle_name'] == ''
    assert part['last_name'] == 'Hamilton'

def test_plea_g():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
p g
""".splitlines()))
    case = cases[0]
    assert case['plea'] == 'guilty'

def test_plea_ng():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
p ng
""".splitlines()))
    case = cases[0]
    assert case['plea'] == 'not guilty'

def test_plea_nc():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
p nc
""".splitlines()))
    case = cases[0]
    assert case['plea'] == 'no contest'

def test_plea_guilty():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
p guilty
""".splitlines()))
    case = cases[0]
    assert case['plea'] == 'guilty'

def test_plea_guitly():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
p guitly
""".splitlines()))
    case = cases[0]
    assert case['plea'] == 'guilty'

def test_plea_ng():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
p not guilty
""".splitlines()))
    case = cases[0]
    assert case['plea'] == 'not guilty'

def test_case_note():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
n this is a test case
""".splitlines()))
    case = cases[0]
    assert case['note'] == 'this is a test case'

# c - cost in $
# f - fine in $
# j - days in jail
# l - days of labor
# m - months of labor
# o - other (use a note)
# p or pd - paid (combination fine, cost, contempt, etc.)
# r - remitted by the mayor
# w - days of labor
    
def test_sentence_rendered_fine():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sr 5 F
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_rendered']) == 1
    except KeyError:
        assert False, 'No sentence rendered found'
    sr = case['sentence_rendered'][0]
    assert sr['type'] == 'fine'
    assert sr['amount'] == 5.0
    assert sr['units'] == '$'

def test_sentence_rendered_cost():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sr 5 C
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_rendered']) == 1
    except KeyError:
        assert False, 'No sentence rendered found'
    sr = case['sentence_rendered'][0]
    assert sr['type'] == 'fine'
    assert sr['amount'] == 5.0
    assert sr['units'] == '$'

def test_sentence_rendered_jail():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sr 5 J
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_rendered']) == 1
    except KeyError:
        assert False, 'No sentence rendered found'
    sr = case['sentence_rendered'][0]
    assert sr['type'] == 'jail'
    assert sr['amount'] == 5.0
    assert sr['units'] == 'days'

def test_sentence_rendered_labor():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sr 5 L
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_rendered']) == 1
    except KeyError:
        assert False, 'No sentence rendered found'
    sr = case['sentence_rendered'][0]
    assert sr['type'] == 'labor'
    assert sr['amount'] == 5.0
    assert sr['units'] == 'days'

def test_sentence_rendered_labor_w():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sr 5 W
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_rendered']) == 1
    except KeyError:
        assert False, 'No sentence rendered found'
    sr = case['sentence_rendered'][0]
    assert sr['type'] == 'labor'
    assert sr['amount'] == 5.0
    assert sr['units'] == 'days'

def test_sentence_rendered_labor_months():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sr 5 M
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_rendered']) == 1
    except KeyError:
        assert False, 'No sentence rendered found'
    sr = case['sentence_rendered'][0]
    assert sr['type'] == 'labor'
    assert sr['amount'] == 5.0
    assert sr['units'] == 'months'

def test_sentence_rendered_remitted():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sr 5 R
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_rendered']) == 1
    except KeyError:
        assert False, 'No sentence rendered found'
    sr = case['sentence_rendered'][0]
    assert sr['type'] == 'remitted'
    assert sr['amount'] == 5.0
    assert sr['units'] == '$'

def test_sentence_rendered_remitted_note():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sr 5 R (note goes here)
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_rendered']) == 1
    except KeyError:
        assert False, 'No sentence rendered found'
    sr = case['sentence_rendered'][0]
    assert sr['type'] == 'remitted'
    assert sr['amount'] == 5.0
    assert sr['units'] == '$'
    assert sr['note'] == 'note goes here'

def test_sentence_rendered_dismissed():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sr Dismissed
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_rendered']) == 1
    except KeyError:
        assert False, 'No sentence rendered found'
    sr = case['sentence_rendered'][0]
    assert sr['type'] == 'dismissed'
    assert sr['amount'] == 0.0
    assert sr['units'] == 'unknown'

def test_sentence_rendered_other_without_note():
    p = vtr.Parser()
    assert_raises(pyparsing.ParseException,
                  list,
                  p.parse("""
b 1902/6
pg 170
c 172
sr o
""".splitlines()))

def test_sentence_rendered_other():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sr o (explain what this means)
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_rendered']) == 1
    except KeyError:
        assert False, 'No sentence rendered found'
    sr = case['sentence_rendered'][0]
    assert sr['type'] == 'other'
    assert sr['amount'] == 0.0
    assert sr['units'] == 'unknown'
    assert sr['note'] == 'explain what this means'





def test_sentence_served_fine():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ss 5 F
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_served']) == 1
    except KeyError:
        assert False, 'No sentence served found'
    ss = case['sentence_served'][0]
    assert ss['type'] == 'fine'
    assert ss['amount'] == 5.0
    assert ss['units'] == '$'

def test_sentence_served_fine_note():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ss 5 F (note goes here)
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_served']) == 1
    except KeyError:
        assert False, 'No sentence served found'
    ss = case['sentence_served'][0]
    assert ss['type'] == 'fine'
    assert ss['amount'] == 5.0
    assert ss['units'] == '$'
    assert ss['note'] == 'note goes here'

def test_sentence_served_fine_date():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ss 5 F 1 Jan 2012
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_served']) == 1
    except KeyError:
        assert False, 'No sentence served found'
    ss = case['sentence_served'][0]
    assert ss['type'] == 'fine'
    assert ss['amount'] == 5.0
    assert ss['units'] == '$'
    assert ss['date'] == datetime.date(2012, 1, 1)

def test_sentence_served_fine_date_note():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ss 5 F 1 Jan 2012 (note goes here)
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_served']) == 1
    except KeyError:
        assert False, 'No sentence served found'
    ss = case['sentence_served'][0]
    assert ss['type'] == 'fine'
    assert ss['amount'] == 5.0
    assert ss['units'] == '$'
    assert ss['date'] == datetime.date(2012, 1, 1)
    assert ss['note'] == 'note goes here'

def test_sentence_served_cost():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ss 5 C
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_served']) == 1
    except KeyError:
        assert False, 'No sentence served found'
    ss = case['sentence_served'][0]
    assert ss['type'] == 'fine'
    assert ss['amount'] == 5.0
    assert ss['units'] == '$'

def test_sentence_served_jail():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ss 5 J
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_served']) == 1
    except KeyError:
        assert False, 'No sentence served found'
    ss = case['sentence_served'][0]
    assert ss['type'] == 'jail'
    assert ss['amount'] == 5.0
    assert ss['units'] == 'days'

def test_sentence_served_labor():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ss 5 L
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_served']) == 1
    except KeyError:
        assert False, 'No sentence served found'
    ss = case['sentence_served'][0]
    assert ss['type'] == 'labor'
    assert ss['amount'] == 5.0
    assert ss['units'] == 'days'

def test_sentence_served_labor_w():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ss 5 W
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_served']) == 1
    except KeyError:
        assert False, 'No sentence served found'
    ss = case['sentence_served'][0]
    assert ss['type'] == 'labor'
    assert ss['amount'] == 5.0
    assert ss['units'] == 'days'

def test_sentence_served_labor_months():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ss 5 M
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_served']) == 1
    except KeyError:
        assert False, 'No sentence served found'
    ss = case['sentence_served'][0]
    assert ss['type'] == 'labor'
    assert ss['amount'] == 5.0
    assert ss['units'] == 'months'

def test_sentence_served_remitted():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ss 5 R
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_served']) == 1
    except KeyError:
        assert False, 'No sentence served found'
    ss = case['sentence_served'][0]
    assert ss['type'] == 'remitted'
    assert ss['amount'] == 5.0
    assert ss['units'] == '$'

def test_sentence_served_remitted_note():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ss 5 R (note goes here)
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_served']) == 1
    except KeyError:
        assert False, 'No sentence served found'
    ss = case['sentence_served'][0]
    assert ss['type'] == 'remitted'
    assert ss['amount'] == 5.0
    assert ss['units'] == '$'
    assert ss['note'] == 'note goes here'

def test_sentence_served_other():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
ss o (explain what this means)
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_served']) == 1
    except KeyError:
        assert False, 'No sentence served found'
    ss = case['sentence_served'][0]
    assert ss['type'] == 'other'
    assert ss['amount'] == 0.0
    assert ss['units'] == 'unknown'
    assert ss['note'] == 'explain what this means'




def test_sentence_contempt():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sc 5
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_contempt']) == 1
    except KeyError:
        assert False, 'No sentence contempt found'
    sc = case['sentence_contempt'][0]
    assert sc['type'] == 'fine'
    assert sc['amount'] == 5.0
    assert sc['units'] == '$'

def test_sentence_contempt_type_fine():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sc 5 F
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_contempt']) == 1
    except KeyError:
        assert False, 'No sentence contempt found'
    sc = case['sentence_contempt'][0]
    assert sc['type'] == 'fine'
    assert sc['amount'] == 5.0
    assert sc['units'] == '$'

def test_sentence_contempt_type_labor():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
sc 5 W
""".splitlines()))
    case = cases[0]
    try:
        assert len(case['sentence_contempt']) == 1
    except KeyError:
        assert False, 'No sentence contempt found'
    sc = case['sentence_contempt'][0]
    assert sc['type'] == 'labor'
    assert sc['amount'] == 5.0
    assert sc['units'] == 'days'



def test_outcome_guilty():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
o g
""".splitlines()))
    case = cases[0]
    assert case['outcome'] == 'guilty'

def test_outcome_guilty_verbose():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
o guilty
""".splitlines()))
    case = cases[0]
    assert case['outcome'] == 'guilty'

def test_outcome_not_guilty():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
o ng
""".splitlines()))
    case = cases[0]
    assert case['outcome'] == 'not guilty'

def test_outcome_not_guilty_verbose():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
o not guilty
""".splitlines()))
    case = cases[0]
    assert case['outcome'] == 'not guilty'
    

def test_outcome_dismissed():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
o d
""".splitlines()))
    case = cases[0]
    assert case['outcome'] == 'dismissed'

def test_outcome_dismissed_verbose():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
o dismissed
""".splitlines()))
    case = cases[0]
    assert case['outcome'] == 'dismissed'

def test_outcome_suspended():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
o s
""".splitlines()))
    case = cases[0]
    assert case['outcome'] == 'suspended'

def test_outcome_suspended_verbose():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
o suspended
""".splitlines()))
    case = cases[0]
    assert case['outcome'] == 'suspended'



def test_gender_male():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
g m
""".splitlines()))
    case = cases[0]
    assert case['gender'] == 'm'

def test_gender_female():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
g f
""".splitlines()))
    case = cases[0]
    assert case['gender'] == 'f'


def test_race_white():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
r w
""".splitlines()))
    case = cases[0]
    assert case['race'] == 'w'

def test_race_white_upper():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
r W
""".splitlines()))
    case = cases[0]
    assert case['race'] == 'w'

def test_race_colored():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
r c
""".splitlines()))
    case = cases[0]
    assert case['race'] == 'c'

def test_race_colored_upper():
    p = vtr.Parser()
    cases = list(p.parse("""
b 1902/6
pg 170
c 172
r C
""".splitlines()))
    case = cases[0]
    assert case['race'] == 'c'
