#!/usr/bin/env python
#
# Copyright 2008 Doug Hellmann.
#
"""VagueTextRecord format parser
"""

from pyparsing import *

# Import system modules
import datetime
import fileinput
import logging
import time

# Import local modules


# Module

log = logging.getLogger(__name__)


def show_parse_action(f):
    """Decorator to show what is going on in a parse action.
    """
    def action(*args):
        if len(args) >= 3:
            s, loc, toks = args[-3:]
            log.debug('%s(s=%r, loc=%s, toks=%s)',
                      f.func_name, s[loc:], loc, toks)
        else:
            log.debug('%s%r', f.func_name, args)
        result = f(*args)
        if result is not None:
            log.debug('%s() -> %r', f.func_name, result)
        return result
    return action


# day month year
DATE = Word(nums) + Word(alphas) + Word(nums)


@show_parse_action
def parse_date(s, loc, toks):
    date_string = ' '.join(toks)
    log.debug('parsing date string %r', date_string)
    for bad, good in [('Sept', 'Sep'), ('July', 'Jul')]:
        date_string = date_string.replace(bad, good)
    parsed_time = time.strptime(date_string, '%d %b %Y')
    date = datetime.datetime(*parsed_time[:3])
    return date
DATE.setParseAction(parse_date)
DATE.setName('date')

# ( anything )
NOTE = (Suppress(Literal('('))
        + Regex(r'[^()]+')
        + Suppress(Literal(')'))
        ).setName('note')


@show_parse_action
def parse_participant(s, loc, toks):
    # full name title=Mr. suffix=Jr. ( anything )
    # don't know how many parts of a name there will be...
    first = middle = last = ''
    parts = toks['fullname'].strip().split()
    last = parts[-1]
    parts = parts[:-1]
    if parts:
        first = parts[0]
        parts = parts[1:]
    middle = ' '.join(parts)
    new_participant = {'first_name': first,
                        'middle_name': middle,
                        'last_name': last,
                        'full_name': toks['fullname'].strip(),
                        'note': toks.get('note', [''])[0],
                        'title': toks.get('title', ''),
                        'alias': toks.get('alias', ''),
                        'suffix': toks.get('suffix', ''),
                        }
    return new_participant
NAME_CHARS = alphas + '.<>[]{},'
NAME = (Regex(r'([^(=]+(\s+|$))+').setResultsName('fullname')
        + Optional(CaselessLiteral('alias=') +
                   Word(NAME_CHARS).setResultsName('alias'))
        + Optional(CaselessLiteral('title=') +
                   Word(NAME_CHARS).setResultsName('title'))
        + Optional(CaselessLiteral('suffix=') +
                   Word(NAME_CHARS).setResultsName('suffix'))
        + Optional(NOTE).setResultsName('note')
        ).setName('name')
NAME.setParseAction(parse_participant)

# c - cost in $
# f - fine in $
# j - days in jail
# l - days of labor
# m - months of labor
# o - other (use a note)
# p or pd - paid (combination fine, cost, contempt, etc.)
# r - remitted by the mayor
# w - days of labor
SENTENCE_TYPE = oneOf('c f j l m o p pd r w', caseless=True)
SENTENCE_TYPE.setName('sentence-type')


def mk_keyword(name):
    """Given a keyword, produce the parser setting to
    recognize and then skip over it.
    """
    return CaselessKeyword(name).suppress()

# "fields" of a case record
ARREST_DATE = (mk_keyword('ad') +
               DATE.setResultsName('date')).setName('arrest-date')
ARRESTING_OFFICER = (mk_keyword('ao') + NAME).setName('arresting-officer')
BOOK = (mk_keyword('b') +
        Word(nums).setResultsName('year') +
        Suppress(Literal('/')) +
        Word(nums).setResultsName('number')).setName('book')
CASE = (mk_keyword('c') +
        Word(printables).setResultsName('number')).setName('case')
DEFENDANT = (mk_keyword('d') + NAME).setName('defendant')
DEFENDANT_VEHICLE = (mk_keyword('dv') +
                     Suppress(White()) +
                     restOfLine.setResultsName('vehicle')
                     ).setName('defendant-vehicle')
DEFENSE_WITNESS = (mk_keyword('dw') + NAME).setName('defense-witness')
GENDER = (mk_keyword('g') +
          oneOf('m f', caseless=True).setResultsName('gender')
          ).setName('gender')
HEARING_DATE = (mk_keyword('hd') +
                DATE.setResultsName('date')).setName('hearing-date')
LOCATION = (mk_keyword('l') +
            Suppress(White()) +
            restOfLine.setResultsName('location')).setName('location')
CASE_NOTE = (mk_keyword('n') +
             Suppress(White()) +
             restOfLine.setResultsName('note')).setName('case-note')
OUTCOME = (mk_keyword('o') +
           (oneOf('g guilty guitly ng d dismissed s suspended',
                  caseless=True)
            | CaselessLiteral('not guilty')
            ).setResultsName('outcome')).setName('outcome')
OTHER_PERSON = (mk_keyword('op') + NAME).setName('other_person')
PLEA = (mk_keyword('p') +
        (oneOf('g ng nc guilty', caseless=True)
         | CaselessLiteral('not guilty')
         ).setResultsName('plea')).setName('plea')
PAGE = (mk_keyword('pg') + Word(nums).setResultsName('number')).setName('page')
RACE = (mk_keyword('r') + oneOf('w c', caseless=True)).setName('race')
SENTENCE_RENDERED = (mk_keyword('sr') + (
    # "other" with a note
    (CaselessLiteral('o').setResultsName('type3') +
     NOTE.setResultsName('note2'))
    # simple full word renderings
    | oneOf('guilty dismissed pd', caseless=True).setResultsName('type2')
    # optional amount, type, & note
    | (Optional(Word(nums + '.')).setResultsName('amount')
       + Optional(SENTENCE_TYPE).setResultsName('type1')
       + Optional(NOTE).setResultsName('note1')
       )
    )).setName('sentence-rendered')
SENTENCE_SERVED = (mk_keyword('ss')
                   + Optional(Word(nums + '.').setResultsName('amount'))
                   + Optional(SENTENCE_TYPE).setResultsName('type')
                   + Optional(DATE.setResultsName('date'))
                   + Optional(NOTE.setResultsName('note'))
                   ).setName('sentence-served')
SENTENCE_CONTEMPT = (mk_keyword('sc')
                     + Word(nums + '.').setResultsName('amount')
                     + Optional(SENTENCE_TYPE.setResultsName('type'))
                     + Optional(NOTE.setResultsName('note'))
                     ).setName('sentence-contempt')
VIOLATION = (mk_keyword('v')
             + Word(printables).setResultsName('violation')
             + Optional(Suppress(White()) + NOTE.setResultsName('note'))
             ).setName('violation')
WITNESS = (mk_keyword('w')
           + NAME
           ).setName('witness')


class Parser(object):
    """Vague text record parser.
    """

    def __init__(self):
        self.case_record_parser = (
            BOOK.copy().setParseAction(self.feed_book)
            | PAGE.copy().setParseAction(self.feed_page)
            | CASE.copy().setParseAction(self.feed_case)
            | ARREST_DATE.copy().setParseAction(self.feed_ad)
            | HEARING_DATE.copy().setParseAction(self.feed_hd)
            | DEFENDANT.copy().setParseAction(self.feed_d)
            | DEFENDANT_VEHICLE.copy().setParseAction(self.feed_dv)
            | VIOLATION.copy().setParseAction(self.feed_v)
            | LOCATION.copy().setParseAction(self.feed_l)
            | ARRESTING_OFFICER.copy().setParseAction(self.feed_ao)
            | WITNESS.copy().setParseAction(self.feed_w)
            | DEFENSE_WITNESS.copy().setParseAction(self.feed_dw)
            | PLEA.copy().setParseAction(self.feed_p)
            | SENTENCE_RENDERED.copy().setParseAction(self.feed_sr)
            | SENTENCE_SERVED.copy().setParseAction(self.feed_ss)
            | SENTENCE_CONTEMPT.copy().setParseAction(self.feed_sc)
            | CASE_NOTE.copy().setParseAction(self.feed_n)
            | OUTCOME.copy().setParseAction(self.feed_o)
            | GENDER.copy().setParseAction(self.feed_g)
            | RACE.copy().setParseAction(self.feed_r)
            | OTHER_PERSON.copy().setParseAction(self.feed_op)
            )
        self.book = None
        self.yield_book = False
        self.page = None
        self.case = None
        self.next_case = None
        self.errors = []
        self._lines = []
        return

    @show_parse_action
    def feed_book(self, s, loc, toks):
        "Start a new book"
        self.book = '%s/%s' % (toks['year'], toks['number'])
        log.info('Set book to %s', self.book)

    @show_parse_action
    def feed_page(self, s, loc, toks):
        "Start a new page in the book"
        self.page = int(toks['number'])

    @show_parse_action
    def feed_case(self, s, loc, toks):
        "Start a new case and prepare the previous one to be emitted."
        if self.case:
            self.next_case = self.case
        self.case = {'book': self.book,
                     'number': toks['number'],
                     'page': self.page,
                     'participants': [],
                     'sentence_rendered': [],
                     'sentence_served': [],
                     'sentence_contempt': [],
                     'defendant': '',
                     }

    @show_parse_action
    def feed_ad(self, s, loc, toks):
        "Arrest date"
        self.case['arrest_date'] = toks['date']

    @show_parse_action
    def feed_hd(self, s, loc, toks):
        "Hearing date"
        self.case['hearing_date'] = toks['date']

    def add_participant(self, role, toks):
        "Add a person's name to the case"
        new_participant = {'role': role}
        new_participant.update(toks)
        log.debug('adding participant %s', new_participant)
        self.case['participants'].append(new_participant)

    @show_parse_action
    def feed_d(self, s=None, loc=None, toks=None):
        "Defendant"
        self.add_participant('defendant', toks[0])
        self.case['defendant'] = toks[0]['full_name']

    @show_parse_action
    def feed_w(self, s, loc, toks):
        "Witness"
        self.add_participant('witness', toks[0])

    @show_parse_action
    def feed_dw(self, s, loc, toks):
        "Defense witness"
        self.add_participant('defense witness', toks[0])

    @show_parse_action
    def feed_ao(self, s=None, loc=None, toks=None):
        "Arresting officer"
        self.add_participant('arresting officer', toks[0])

    @show_parse_action
    def feed_dv(self, s, loc, toks):
        "Defendant vehicle"
        self.case['vehicle'] = toks['vehicle']

    @show_parse_action
    def feed_v(self, s, loc, toks):
        "Violation code"
        self.case['violation'] = toks['violation']
        self.case['violation_note'] = toks.get('note', [''])[0]

    @show_parse_action
    def feed_l(self, s, loc, toks):
        "Location"
        self.case['location'] = toks['location']

    @show_parse_action
    def feed_p(self, s, loc, toks):
        "Plea"
        found_plea = toks['plea'].lower()
        plea = {'g': 'guilty',
                'ng': 'not guilty',
                'nc': 'no contest',
                'u': 'unknown',
                'guitly': 'guilty',  # common typo
                 }.get(found_plea, found_plea)
        self.case['plea'] = plea

    @show_parse_action
    def feed_n(self, s, loc, toks):
        "Case note"
        self.case.setdefault('note', []).append(toks['note'])

    @show_parse_action
    def feed_o(self, s, loc, toks):
        "Outcome"
        outcomes = {'g': 'guilty',
                    'ng': 'not guilty',
                    'd': 'dismissed',
                    's': 'suspended',
                    }
        found = toks['outcome'].lower()
        self.case['outcome'] = outcomes.get(found, found)

    SENTENCE_TYPES = {
        'c': ('fine', '$'),
        'f': ('fine', '$'),
        'j': ('jail', 'days'),
        'l': ('labor', 'days'),
        'm': ('labor', 'months'),
        'o': ('other', 'unknown'),
        'p': ('paid', '$'),
        'pd': ('paid', '$'),
        'r': ('remitted', '$'),
        'w': ('labor', 'days'),
        }

    @show_parse_action
    def feed_sr(self, s, loc, toks):
        amount = float(toks.get('amount', 0))

        if toks.get('type1'):
            found_sent_type = toks.get('type1')
            note = toks.get('note1', [''])[0]
        elif toks.get('type2'):
            found_sent_type = toks.get('type2')
            note = ''
        elif toks.get('type3'):
            found_sent_type = toks.get('type3')
            note = toks.get('note2', [''])[0]
        else:
            found_sent_type = 'unknown'
            note = ''

        converted_sent_type, sent_units = self.SENTENCE_TYPES.get(
            found_sent_type,
            (found_sent_type, 'unknown')
            )
        new_sent = {'type': converted_sent_type,
                    'units': sent_units,
                    'amount': amount,
                    'note': note,
                    }

        if converted_sent_type == 'other' and not note:
            raise ValueError('Invalid sentence rendered, no note for "other"')

        self.case['sentence_rendered'].append(new_sent)

    @show_parse_action
    def feed_ss(self, s, loc, toks):
        found_sent_type = toks.get('type')
        converted_sent_type, sent_units = self.SENTENCE_TYPES.get(
            found_sent_type,
            (found_sent_type, 'unknown')
            )

        new_sent = {
            'amount': float(toks.get('amount', 0)),
            'type': converted_sent_type,
            'units': sent_units,
            'note': toks.get('note', [''])[0],
            'date': toks.get('date', None),
            }

        self.case['sentence_served'].append(new_sent)

    @show_parse_action
    def feed_sc(self, s, loc, toks):
        found_sent_type = toks.get('type', 'f')
        converted_sent_type, sent_units = self.SENTENCE_TYPES.get(
            found_sent_type,
            (found_sent_type, 'unknown')
            )

        new_sent = {
            'amount': float(toks.get('amount', 0)),
            'type': converted_sent_type,
            'units': sent_units,
            'note': toks.get('note', [''])[0],
            }

        self.case['sentence_contempt'].append(new_sent)

    @show_parse_action
    def feed_g(self, s, loc, toks):
        "Defendant's gender"
        self.case['gender'] = toks['gender'].lower()

    @show_parse_action
    def feed_r(self, s, loc, toks):
        "Defendant's race"
        self.case['race'] = toks[-1].lower()

    @show_parse_action
    def feed_op(self, s=None, loc=None, toks=None):
        "Other person"
        self.add_participant('other', toks[0])

    def validate_case(self, case, line_num):
        defendants = [p
                      for p in case['participants']
                      if p['role'] == 'defendant'
                      ]
        if not defendants:
            self.errors.append((line_num,
                                '',
                                'No defendant found for %s' % case['number'],
                                )
                               )
        return

    def prepare_case(self, case, line_num):
        """Validate and fill in default values for a case.
        """
        # Look for validation warnings
        self.validate_case(case, line_num)
        # Set default values for dates
        for sentence in case.get('sentences', []):
            if (not sentence.get('date')) and case.get('hearing_date'):
                sentence['date'] = case['hearing_date']
        # Set the year for the case
        ad = case.get('arrest_date')
        case['year'] = (ad.date().year
                        if ad
                        else int(case['book'].split('/')[0])
                        )
        # Merge the notes
        case['note'] = '\n'.join(case.get('note', []))
        # Record the raw version of the input that lead to this case
        case['lines'] = self._lines[:]
        return

    def parse(self, lines, continueOnError=True):
        """The public API.

        The lines argument should be an iterable that returns strings
        (a file, fileinput, list, etc.).

        If continueOnError is true the parser logs any
        errors and keeps going.
        """
        for num, line in enumerate(lines, 1):
            line = line.strip()
            log.debug(line)
            if line:
                try:
                    self._lines.append((num, line))
                    self.case_record_parser.parseString(line)
                    if self.next_case:
                        self.prepare_case(self.next_case, num)
                        yield self.next_case
                        self.next_case = None
                        self._lines = []
                except (ParseException, ValueError) as err:
                    self.errors.append((num, line, unicode(err)))
                    log.error('Parse error processing %r: %s', line, err)
                    if not continueOnError:
                        raise
                    continue
        # Make sure we yield the last case in the input
        if self.case:
            self.prepare_case(self.case, num)
            yield self.case

if __name__ == '__main__':
    import pprint
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)-8s %(message)s',
                        )
    parser = Parser()
    for record in parser.parse(fileinput.input()):
        #log.info('New case: %s', record)
        print '-' * 80
        pprint.pprint(record)
