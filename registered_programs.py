#! /usr/local/bin/python3
"""
  Scrapes the NYS DOE website for registered academic programs at CUNY colleges.

      This is a two-phase process:
      I. Make a POST request to http://www.nysed.gov/coms/rp090/IRPS2A to get a web page listing
      all programs for a college, and extract the numeric program codes and Unit Codes.
      II. Make a GET request to http://www.nysed.gov/COMS/RP090/IRPSL3 for each of the program
      codes retrieved from Phase I, and analyze each page returned to extract the information needed
      to generate the desired for output, which may be a .csv file, a HTML table, or a database
      table.

April 2019:
      Unit Code is new: “Applications for program revisions, title changes and program
      discontinuances should be submitted to the NYSED office that originally registered the
      program.”
        OP:   Office of the Professions
        OCUE: Office of College and University Evaluation

"""
import sys
import re
import argparse
from datetime import date

import requests
from lxml.html import document_fromstring
import cssselect

import csv

import psycopg2
from psycopg2.extras import NamedTupleCursor

from program import Program
from known_institutions import known_institutions

__author__ = 'Christopher Vickery'
__version__ = 'April 2019'


def detail_lines(all_lines, debug=False):
  """ Filter out unwanted lines from a details web page for a program code, and yield the others.
  """
  lines = all_lines.splitlines()
  for line in lines:
    if re.search(r'^\s+\d{5}\s+|FOR AWARD|PROGRAM|CERTIFICATE|M/A|M/I', line):
      next_line = line.replace('<H4><PRE>', '').strip()
      if debug:
        print(next_line)
      yield next_line


def fix_title(str):
  """ Create a better titlecase string, taking specifics of this dataset into account.
  """
  return (str.strip(' *')
             .title()
             .replace('Cuny', 'CUNY')
             .replace('Mhc', 'MHC')
             .replace('\'S', '’s')
             .replace('1St', '1st')
             .replace('6Th', '6th')
             .replace(' And ', ' and '))


def lookup_programs(institution, verbose=False, debug=False):
  """ Scrape info about academic programs registered with NYS from the Department of Education
      website. Create a Program object for each program_code.
  """
  institution_id, institution_name, is_cuny = known_institutions[institution]

  # Phase I: Get the program code, title, award, hegis, and unit code for all programs
  # registered for the institution.
  if verbose:
    print(f'Fetching list of registered programs for {institution_name} ...', file=sys.stderr)
  r = requests.post('http://www.nysed.gov/coms/rp090/IRPS2A', data={'SEARCHES': '1',
                                                                    'instid': f'{institution_id}'})
  html_document = document_fromstring(r.content)
  # the program codes and unit codes are inside H4 elements, in the following sequence:
  #   PROGRAM CODE  : 36256 - ...
  #   PROGRAM TITLE : [title text] AWARD : [award text]
  #   INST.NAME/CITY .[name and address, ignored].. HEGIS : [hegis string for this award]
  #   FORMAT ... (Not always present; ignored.)
  #   UNIT CODE     : OCUE|OP
  h4s = [h4.text_content() for h4 in html_document.cssselect('h4')]
  # [Waiting for assignment expressions in python 3.8 (PEP 572)]
  this_award = None
  for h4 in h4s:

    matches = re.search(r'PROGRAM CODE\s+:\s+(\d+) -.+PROGRAM TITLE\s+:\s+(.+)AWARD : (\S+\s?\S*)',
                        h4)
    if matches:
      program_code = matches.group(1)
      p = Program(program_code)
      this_title = fix_title(matches.group(2))
      this_award = matches.group(3).strip()
      continue

    matches = re.search(r'HEGIS : (\S+)', h4)
    if matches:
      this_hegis = matches.group(1)
      p.new_variant(this_award, this_hegis, title=this_title)
      continue

    if 'UNIT CODE' in h4:
      matches = re.match(r'\s*UNIT CODE\s*:\s*(.+)\s*', h4)
      assert matches is not None, f'\nUnrecognized unit code line: {h4}'
      p.unit_code = matches.group(1).strip()
      continue

  if verbose:
    num_programs = len(Program.programs)
    len_num = len(str(num_programs))
    print(f'Found {num_programs} registered programs.', file=sys.stderr)
    print('Fetching details...', file=sys.stderr)

  if debug:
    for p in Program.programs:
      program = Program.programs[p]
      print(program.program_code, program.unit_code)
      for v in program.variants:
        print(v, program.values(v))

  # Phase II: Get the details for each program found in Phase I
  programs_counter = 0
  for p in Program.programs:
    program = Program.programs[p]
    programs_counter += 1
    if verbose:
      print(f'Program code: {p} ({programs_counter:{len_num}}/{num_programs})\r',
            end='', file=sys.stderr)

    for_award = None
    r = requests.get(f'http://www.nysed.gov/COMS/RP090/IRPSL3?PROGCD={program.program_code}')
    for line in detail_lines(r.text):
      # Use the first token on a line to determine the type of line.
      tokens = line.split()
      token = tokens[0]

      # First token is a numeric string (Program Code #.).
      if token.isdecimal() or token == 'M/A':
        # Extract program_code, title, hegis_code, award, institution.
        matches = re.match(r'\s*\d+|M/A(.+)(\d{4}\.\d{2})\s+(\S+\s?\S*)\s+(.+)', line)
        if matches is None:
          sys.exit(f'\nUnable to parse program code line for program code {program_code}:\n{line}')
        # if Check the title and hegis for the award. Always set the institution.
        program_title = fix_title(matches.group(1))
        program_hegis = matches.group(2)
        program_award = matches.group(3).strip()
        program_institution = matches.group(4)
        if debug:
          print(f'{program.program_code}: "{program_title}" {program_hegis}'
                f' {program_award} "{program_institution}"')
        # Be sure this variant exists
        this_variant = program.new_variant(program_award, program_hegis, title=program_title)

        if program_institution == institution_name:
          program.variants[this_variant].institution = institution.upper()
        else:
          for key in known_institutions.keys():
            if program_institution == known_institutions[key][1]:
              program.variants[this_variant].institution = key.upper()
              break
        assert program.variants[this_variant].institution is not None
        continue

      # if token == 'M/A':
      #   # line_type.multiple_awards
      #   # Extract title, hegis, award, and institution
      #   matches = re.match(r'\s*M/A(.+)(\d{4}\.\d{2})\s+(\S+\s?\S*)\s+(.+)', line)
      #   if matches is None:
      #     sys.exit(f'\nUnable to parse M/A line for program code {program_code}:\n{line}')
      #   program_title = fix_title(matches.group(1))
      #   program_hegis = matches.group(2)
      #   program_award = matches.group(3).strip()
      #   program_institution = matches.group(4)
      #   if debug:
      #     print(f'{program.program_code}: "{program_title}" {program_hegis}'
      #           f' {program_award} "{program_institution}"')
      #   # Be sure this variant exists
      #   this_variant = program.new_variant(program_award, program_hegis, title=program_title)
      #   if program_institution == institution_name:
      #     program.variants[this_variant].institution = institution.upper()
      #   else:
      #     for key in known_institutions.keys():
      #       if program_institution == known_institutions[key][1]:
      #         program.variants[this_variant].institution = key.upper()
      #         break
      #   assert program.variants[this_variant].institution is not None
      #   continue

      """
      It's a mess. Program variants are identified by award, hegis, AND institution. The M/I
      lines, when the award is not NOT-GRANTING tell you when you need a new variant. Then the FOR
      AWARD lines have to apply to all variants that share that award (even if they have different
      hegis’s, I think.)
      """

      if token == 'M/I':
        # # Multi-institution lines add no new information about a program because multi-award lines
        # # already tell what the institution(s) are.
        # # But parsing code remains ... “just in case”
        # # Extract hegis, award, institution
        # #   But there is no hegis if the award is NOT-GRANTING
        # if 'NOT-GRANTING' in line:
        #   program_hegis = None
        #   program_award = None
        #   program_institution = line.split('NOT-GRANTING ')[1].strip()
        # else:
        #   matches = re.search(r'(\d{4}.\d{2})\s+(\S+\s?\S*)\s+(.*)', line)
        #   if matches is None:
        #     sys.exit(f'\nUnable to parse M/I line for program code {program.program_code}:{line}')
        #   program_hegis = matches.group(1)
        #   program_award = matches.group(2)
        #   program_institution = matches.group(3).strip()
        # if debug:
        #   print('M/I:', program_hegis, program_award, program_institution)
        continue

      if token == 'FOR':
        # Extract award. The following lines will not be of interest unless the award is in the list
        # for this institution.
        for_award = re.match(r'\s*FOR AWARD\s*--(.*)', line).group(1).strip()
        assert for_award in program.awards, f'{for_award} not in {program.awards}'

      if token.startswith('CERTIFICATE') and for_award is not None:
        # Extract certificate tuple {name, type, date} if there is one.
        cert_info = re.sub(r'\s+', ' ', line.split(':')[1].strip())
        if cert_info.startswith('NONE'):
          cert_info = ''
        program.awards[for_award].certificate_license = cert_info
        continue

      if token == 'PROGRAM' and tokens[1] == 'FINANCIAL' and for_award is not None:
        # Extract three booleans.
        matches = re.search(r'(YES|NO).+(YES|NO).+(YES|NO)', line)
        if matches is None:
          sys.exit('\nUnable to parse eligibility line for program code {}:\n{line}'
                   .format(program.program_code))
        program.awards[for_award].tap = matches.group(1)
        program.awards[for_award].apts = matches.group(2)
        program.awards[for_award].vvta = matches.group(3)
        continue

      if token == 'PROGRAM' and tokens[1] == 'PROFESSIONAL' and for_award is not None:
        # Extract text, if any.
        program.accreditation = line.split(':')[1].strip()

      if token == 'PROGRAM' and tokens[1] == 'FIRST' and for_award is not None:
        matches = re.search(r'DATE:\s+(\S+).+DATE:\s+(\S+)', line)
        if matches is None:
          sys.exit('\nUnable to parse registration dates for program code {}:\n{}'
                   .format(program.program_code, line))
        first_date = matches[1]
        last_date = matches[2]
        if (program.awards[for_award].first_registration_date is None
                or first_date.replace('PRE-', '19')
                < program.awards[for_award].first_registration_date):
          program.awards[for_award].first_registration_date = first_date
        if (program.awards[for_award].last_registration_date is None
                or last_date > program.awards[for_award].last_registration_date):
          program.awards[for_award].last_registration_date = last_date
  if verbose:
    print()
  return Program.programs


""" Provision for running script from the command line.
"""
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='''
                                   Scrape the NYS Department of Education website for information
                                   about academic programs registered for CUNY colleges.''',
                                   epilog='''
                                   NOTE: Database option not implemented yet.''')
  parser.add_argument('institution')
  parser.add_argument('-u', '--update_db', action='store_true', default=False,
                      help='update info for this institution in the registered_programs database')
  parser.add_argument('-w', '--html', action='store_true', default=False,
                      help='generate a html table suitable for the web')
  parser.add_argument('-c', '--csv', action='store_true', default=False,
                      help='generate a CSV table')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-v', '--verbose', action='store_true', default=False)
  args = parser.parse_args()

  if not args.debug and not args.csv and not args.html and not args.update_db:
    sys.exit('No output options: nothing to do.')

  institution = args.institution.lower().strip('10')
  programs = lookup_programs(institution, debug=args.debug, verbose=args.verbose)
  if programs is not None:
    if args.csv:
      # Generate spreadsheet
      #
      file_name = institution.upper() + '_' + date.today().isoformat() + '.csv'
      with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Program Code', 'Registration Office'] + Program.headings)
        for p in Program.programs:
          program = programs[p]
          for award, hegis in program.awards.keys():
            writer.writerow([program.program_code, program.unit_code]
                            + program.values(award, hegis))
    if args.html:
      print(Program.html(institution.upper()))
    if args.update_db:
      db = psycopg2.connect('dbname=cuny_courses')
      cursor = db.cursor(cursor_factory=NamedTupleCursor)
      cursor.execute('delete from registered_programs where target_institution=%s',
                     (institution,))
      print('Replacing {} entries for {} with info for {} programs.'
            .format(cursor.rowcount, institution.upper(), len(Program.programs)))
      for p in Program.programs:
        program = programs[p]
        for award, hegis in program.awards.keys():
          values = [institution,
                    program.program_code,
                    program.unit_code] + program.values(award, hegis)
          cursor.execute('insert into registered_programs values(' + ', '.join(['%s'] * len(values))
                         + ')', values)
      db.commit()
      db.close()

  else:
    sys.exit('lookup_programs failed')
