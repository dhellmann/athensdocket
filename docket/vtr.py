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
import re
import string
import sys
import time

# Import local modules


# Module

log = logging.getLogger(__name__)

# day month year
DATE = Word(nums) + Word(alphas) + Word(nums)
def parse_date(s, loc, toks):
    date_string = ' '.join(toks)
    log.debug('parsing date string %r', date_string)
    for bad, good in [ ('Sept', 'Sep'), ('July', 'Jul')]:
        date_string = date_string.replace(bad, good)
    parsed_time = time.strptime(date_string, '%d %b %Y')
    date = datetime.date(*parsed_time[:3])
    return date
DATE.setParseAction(parse_date)

# ( anything )
NOTE = ( Suppress(Literal('('))
         + Regex(r'[^()]+')
         + Suppress(Literal(')'))
         )

# full name title=Mr. suffix=Jr. ( anything )
# don't know how many parts of a name there will be...
NAME_CHARS = alphas + '.<>[]{},'
NAME = (Regex(r'([^(=]+(\s+|$))+').setResultsName('fullname')
        + Optional(CaselessLiteral('title=') + Word(NAME_CHARS).setResultsName('title'))
        + Optional(CaselessLiteral('suffix=') + Word(NAME_CHARS).setResultsName('suffix'))
        + Optional(NOTE).setResultsName('note')
        )

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

# "fields" of a case record
ARREST_DATE = CaselessKeyword('ad') + DATE.setResultsName('date')
ARRESTING_OFFICER = CaselessKeyword('ao') + NAME
BOOK = CaselessKeyword('b') + Word(nums).setResultsName('year') + Suppress(Literal('/')) + Word(nums).setResultsName('number')
CASE = CaselessKeyword('c') + Word(printables).setResultsName('number')
DEFENDANT = CaselessKeyword('d') + NAME.setResultsName('name') + Optional(NOTE.setResultsName('note'))
DEFENDANT_VEHICLE = CaselessKeyword('dv') + Suppress(White()) + restOfLine.setResultsName('vehicle')
DEFENSE_WITNESS = CaselessKeyword('dw') + NAME + Optional(NOTE.setResultsName('note'))
GENDER = CaselessKeyword('g') + oneOf('m f', caseless=True).setResultsName('gender')
HEARING_DATE = CaselessKeyword('hd') + DATE.setResultsName('date')
LOCATION = CaselessKeyword('l') + Suppress(White()) + restOfLine.setResultsName('location')
CASE_NOTE = CaselessKeyword('n') + Suppress(White()) + restOfLine.setResultsName('note')
OUTCOME = CaselessKeyword('o') + (oneOf('g guilty ng d dismissed s suspended', caseless=True) | CaselessLiteral('not guilty')).setResultsName('outcome')
PLEA = CaselessKeyword('p') + (oneOf('g ng nc guilty', caseless=True)
                               | CaselessLiteral('not guilty')).setResultsName('plea')
PAGE = CaselessKeyword('pg') + Word(nums).setResultsName('number')
RACE = CaselessKeyword('r') + oneOf('w c', caseless=True)
SENTENCE_RENDERED = CaselessKeyword('sr') + (
    (Word(nums + '.').setResultsName('amount')
     + Optional(SENTENCE_TYPE).setResultsName('type1')
     + Optional(NOTE).setResultsName('note1')
     )
    | oneOf('guilty dismissed pd', caseless=True).setResultsName('type2')
    | CaselessLiteral('o').setResultsName('type3') + NOTE.setResultsName('note2')
    )
SENTENCE_SERVED = ( CaselessKeyword('ss')
                    + Optional(Word(nums + '.').setResultsName('amount'))
                    + Optional(SENTENCE_TYPE).setResultsName('type')
                    + Optional(DATE.setResultsName('date'))
                    + Optional(NOTE.setResultsName('note'))
                    )
SENTENCE_CONTEMPT = (CaselessKeyword('sc')
                     + Word(nums + '.').setResultsName('amount')
                     + Optional(SENTENCE_TYPE.setResultsName('type'))
                    + Optional(NOTE.setResultsName('note'))
                     )
VIOLATION = CaselessKeyword('v') + Word(printables).setResultsName('violation') + Optional(Suppress(White()) + NOTE.setResultsName('note'))
WITNESS = CaselessKeyword('w') + NAME + Optional(NOTE.setResultsName('note'))

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
            )
        self.book = None
        self.yield_book = False
        self.page = None
        self.case = None
        self.next_case = None
        self.errors = []
        return

    def feed_book(self, s, loc, toks):
        "Start a new book"
        log.debug('feed book: %r', toks)
        self.book = '%s/%s' % (toks['year'], toks['number'])
        log.info('Set book to %s', self.book)

    def feed_page(self, s, loc, toks):
        "Start a new page in the book"
        log.debug('feed page: %r', toks)
        self.page = int(toks['number'])

    def feed_case(self, s, loc, toks):
        "Start a new case and prepare the previous one to be emitted."
        log.debug('feed case: %r', toks)
        if self.case:
            self.next_case = self.case
        self.case = { 'book': self.book,
                      'number': toks['number'],
                      'page': self.page,
                      'participants':[],
                      'sentence_rendered':[],
                      'sentence_served':[],
                      'sentence_contempt':[],
                      }

    def feed_ad(self, s, loc, toks):
        "Arrest date"
        self.case['arrest_date'] = toks['date']

    def feed_hd(self, s, loc, toks):
        "Hearing date"
        self.case['hearing_date'] = toks['date']

    def add_participant(self, role, toks):
        "Add a person's name to the case"
        first = middle = last = ''
        parts = toks['fullname'].strip().split()
        last = parts[-1]
        parts = parts[:-1]
        if parts:
            first = parts[0]
            parts = parts[1:]
        middle = ' '.join(parts)
        new_participant = { 'role': role,
                            'first_name':first,
                            'middle_name':middle,
                            'last_name':last,
                            'full_name':toks['fullname'].strip(),
                            'note': toks.get('note', [''])[0],
                            'title': toks.get('title', ''),
                            'suffix': toks.get('suffix', ''),
                            }
        log.debug('adding participant %s', new_participant)
        self.case['participants'].append( new_participant )

    def feed_d(self, s=None, loc=None, toks=None):
        "Defendant"
        log.debug('feed_d %r %s %s', s, loc, toks)
        self.add_participant('defendant', toks)

    def feed_w(self, s, loc, toks):
        "Witness"
        log.debug('feed_w %r, %s, %s', s, loc, toks)
        self.add_participant('witness', toks)

    def feed_dw(self, s, loc, toks):
        "Defense witness"
        log.debug('feed_dw %r, %s, %s', s, loc, toks)
        self.add_participant('defense witness', toks)

    def feed_ao(self, s=None, loc=None, toks=None):
        "Arresting officer"
        log.debug('feed_ao %r %s %s', s, loc, toks)
        self.add_participant('arresting officer', toks)

    def feed_dv(self, s, loc, toks):
        "Defendant vehicle"
        log.debug('feed_dv %r, %s, %s', s, loc, toks)
        self.case['vehicle'] = toks['vehicle']

    def feed_v(self, s, loc, toks):
        "Violation code"
        log.debug('feed_v %r, %s, %s', s, loc, toks)
        self.case['violation'] = toks['violation']
        self.case['violation_note'] = toks.get('note', [''])[0]

    def feed_l(self, s, loc, toks):
        "Location"
        log.debug('feed_l %r, %s, %s', s, loc, toks)
        self.case['location'] = toks['location']

    def feed_p(self, s, loc, toks):
        "Plea"
        log.debug('feed_p %r, %s, %s', s, loc, toks)
        found_plea = toks['plea'].lower()
        plea = { 'g':'guilty',
                 'ng':'not guilty',
                 'nc':'no contest',
                 'u':'unknown',
                 'guitly':'guilty', # common typo
                 }.get(found_plea, found_plea)
        self.case['plea'] = plea

    def feed_n(self, s, loc, toks):
        "Case note"
        log.debug('feed_n %r, %s, %s', s, loc, toks)
        self.case['note'] = toks['note']

    def feed_o(self, s, loc, toks):
        "Outcome"
        log.debug('feed_o %r, %s, %s', s, loc, toks)
        outcomes = { 'g':'guilty',
                     'ng':'not guilty',
                     'd':'dismissed',
                     's':'suspended',
                     }
        found = toks['outcome'].lower()
        self.case['outcome'] = outcomes.get(found, found)

    SENTENCE_TYPES = {
        'c':('fine', '$'),
        'f':('fine', '$'),
        'j':('jail', 'days'),
        'l':('labor', 'days'),
        'm':('labor', 'months'),
        'o':('other', 'unknown'),
        'p':('paid', '$'),
        'pd':('paid', '$'),
        'r':('remitted', '$'),
        'w':('labor', 'days'),
        }
    
    def feed_sr(self, s, loc, toks):
        log.debug('feed_sr %r, %s, %s', s, loc, toks)

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
        log.debug('here')

        converted_sent_type, sent_units = self.SENTENCE_TYPES.get(found_sent_type,
                                                         (found_sent_type, 'unknown')
                                                         )
        new_sent = { 'type': converted_sent_type,
                     'units': sent_units,
                     'amount': float(toks.get('amount', '0')),
                     'note': note,
                     }
        self.case['sentence_rendered'].append(new_sent)
    
    def feed_ss(self, s, loc, toks):
        log.debug('feed_ss %r, %s, %s', s, loc, toks)

        found_sent_type = toks.get('type')
        converted_sent_type, sent_units = self.SENTENCE_TYPES.get(found_sent_type,
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
    
    def feed_sc(self, s, loc, toks):
        log.debug('feed_sc %r, %s, %s', s, loc, toks)

        found_sent_type = toks.get('type', 'f')
        converted_sent_type, sent_units = self.SENTENCE_TYPES.get(found_sent_type,
                                                         (found_sent_type, 'unknown')
                                                         )

        new_sent = {
            'amount': float(toks.get('amount', 0)),
            'type': converted_sent_type,
            'units': sent_units,
            'note': toks.get('note', [''])[0],
            }
        
        self.case['sentence_contempt'].append(new_sent)

    def feed_g(self, s, loc, toks):
        "Defendant's gender"
        log.debug('feed_g %r, %s, %s', s, loc, toks)
        self.case['gender'] = toks['gender'].lower()

    def feed_r(self, s, loc, toks):
        "Defendant's race"
        log.debug('feed_r %r, %s, %s', s, loc, toks)
        self.case['race'] = toks[-1].lower()

    def parse(self, lines, continueOnError=True):
        """The public API.

        The lines argument should be an iterable that returns strings
        (a file, fileinput, list, etc.).

        If continueOnError is true the parser logs any
        errors and keeps going.
        """
        for num, line in enumerate(lines):
            line = line.strip()
            log.debug(line)
            if line:
                try:
                    self.case_record_parser.parseString(line)
                except ParseException as err:
                    self.errors.append((num, line, unicode(err)))
                    log.error('Parse error processing %r: %s', line, err)
                    if not continueOnError:
                        raise
                    continue
                if self.next_case:
                    yield self.next_case
                    self.next_case = None
        # Make sure we yield the last case in the input
        if self.case:
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
        
