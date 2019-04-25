#! /usr/local/bin/python3
""" Create a spreadsheet giving information for each NYSDOE-approved academic program
    at Queens College.

  Scrapes the QC information from the NYS DOE website.

  The spreadsheet lines consist of the following columns. The combination of values listed as
  the primary key are guaranteed to be unique.

  Primary Key
    program_code, program_name, HEGIS_code, award, institution
  Fields
    certificate_licenses_titles_types, TAP_eligible, APTS_eligible, WTA_eligible, accreditation,
    Unit Code

April 2019:
      Unit Code is new. “Applications for program revisions, title changes and program
      discontinuances should be submitted to the NYSED office that originally registered the
      program.”
        OP:   Office of the Professions
        OCUE: Office of College and University Evaluation
      The Unit Code is on the same page as the program code, so the functionality of the bash
      script that used to generate a program_codes.out file has now been folded into this script in
      order to pick up this new information.

      That is, this is a two-step process:
      1. Make a POST request to http://www.nysed.gov/coms/rp090/IRPS2A to get a web page listing
      all QC programs, and extract the numeric program codes and Unit Codes.
      2. Make a GET request to http://www.nysed.gov/COMS/RP090/IRPSL3 for each of the program
      codes retrieved from Step 1, and analyze each page returned to extract the information needed
      to generate the spreadsheet to generate for output.

January 2016:
Deductions, based on examination of the program_codes.out file:
  M/A is for Multiple Awards: the same program code may be associated with more than one degree
  M/I is for Multiple Institutions: the same program may be associated with more than one
      institution, which may use different HEGIS codes and/or awards. If the institution award
      is "NON GRANTING" there is no HEGIS code for that institution.

Input file structure:
  One program code line: code number; program title; hegis; award; institution
  Zero or more M/I or M/A lines
    M/I WITH - - - ... -> hegis (may be empty); award (may be NOT-GRANTING); institution
      If there is an award other than NOT-GRANTING, it gets added to the list of awards for the
      program, and there must be one FOR AWARD line for each award in this list.
  For each award:
    For award (BA, MA, etc.)
      Program first and last registration dates
      Certificate, etc.
      Program registration dates
      Financial Aid
      Accreditation

Algorithm:
  Read a line, and extract line_type (see the Line Type enum)
  Check previous line_type against this line_type to make sure a valid sequence is taking place.
  Then go to the particular algorithm step given below based on this line_type.

  program:                Extract program_code, program_name, hegis_code, award, institution;
                          check for duplicate program code;
  multiple_awards:        Extract program_name, HEGIS, award, institution. Add to respective sets.
  multiple_instituitions: Extract HEGIS, award, institution.
  for_award:              Extract award.
  certificate_etc:        Extract certificate tuple {name, type, date} if there is one.
  program first:          Extract first and last registration dates
  financial_aid:          Extract three booleans.
  accreditation:          Extract text, if any.

Expect lines in a detail report in the following sequence:
  Always:
    Program Code No. [Program Name] [HEGIS code] [Degree] [Institution]
  Optional:
    M/I WITH - - - > [Degree] [Institution]
    M/A [Program Name] [HEGIS code] [Degree] [Institution]
  Always:
    FOR AWARD -- [Degree]
    CERTIFICATES/LICENSES TITLES AND TYPES: [text]
    PROGRAM FIRST REG DATE: [first_reg_date] LAST REG DATE: [last_reg_date]
    PROGRAM FINANCIAL AID ELIGIBILITY: [TAP: YES|NO] [APTS: YES|NO] [VVTA: YES|NO]
    PROGRAM PROFESSIONAL ACCREDITATION: [text]

"""
import sys
import re
import argparse
from datetime import date

import requests
from lxml.html import document_fromstring
import cssselect

import csv

from program import Program
from cuny_institutions import cuny_institutions

__author__ = 'Christopher Vickery'
__version__ = 'April 2019'


def detail_lines(all_lines, debug=False):
  """ Filter out unwanted lines from a details web page for a program code, and generate the others.
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
             .replace('Mhc', 'MHC')
             .replace('\'S', '’s')
             .replace('1St', '1st')
             .replace('6Th', '6th')
             .replace(' And ', ' and ')
             .replace('Cuny', 'CUNY'))


def update_program(program, institution, institution_name, award=None, title=None, hegis=None):
  """ Update info for a program.
      It matters whether the institution matches the institution_name or not.
  """
  if institution == institution_name:
    program.institution = fix_title(institution)
    if award is not None:
      program.award = award
    if title is not None:
      program.title = fix_title(title)
    if hegis is not None:
      program.hegis = hegis
  else:
    program.other_institution = f'{fix_title(institution)} “{fix_title(title)}” {hegis}, ({award})'


def lookup_programs(institution, verbose=False, debug=False):
  """ Scrape info about academic programs registered with NYS from the Department of Education
      website.
  """
  institution_id, institution_name = cuny_institutions[institution]
  # Fetch the web page with program code, title, award, hegis, and unit code for all programs
  # registered for the institution.
  if verbose:
    print(f'Fetching list of registered programs for {institution_name} ...', file=sys.stderr)
  r = requests.post('http://www.nysed.gov/coms/rp090/IRPS2A', data={'SEARCHES': '1',
                                                                    'instid': f'{institution_id}'})
  html_document = document_fromstring(r.content)
  # the program codes and unit codes are inside H4 elements, in the following sequence:
  #   PROGRAM CODE  : 36256 - ...
  #   PROGRAM TITLE : [title text] AWARD : [award text]
  #   INST.NAME/CITY ... (Includes hegis, but get that from details; ignored.)
  #   FORMAT ... (Not always present; ignored.)
  #   UNIT CODE     : OCUE|OP
  h4s = [h4.text_content() for h4 in html_document.cssselect('h4')]
  # [Waiting for assignment expressions in python 3.8 (PEP 572)]
  # h4s = [h4_line for h4 in html_document.cssselect('h4') if 'CODE' in h4_line := h4.text_content()]

  for h4 in h4s:
    if 'PROGRAM CODE' in h4 and 'PROGRAM TITLE ORDER' not in h4:
      matches = re.match(r'^\s*PROGRAM CODE\s*:\s*(\d+)', h4)
      assert matches is not None, f'Unrecognized program code line: {h4}'
      p = Program(matches.group(1))

    if 'UNIT CODE' in h4:
      matches = re.match(r'\s*UNIT CODE\s*:\s*(.+)\s*', h4)
      assert matches is not None, f'Unrecognized unit code line: {h4}'
      p.unit_code = matches.group(1).strip()
  if verbose:
    num_programs = len(Program.programs)
    len_num = len(str(num_programs))
    print(f'Found {num_programs} registered programs.', file=sys.stderr)
    print('Fetching details...', file=sys.stderr)

  programs_counter = 0
  for p in Program.programs:
    program = Program.programs[p]
    programs_counter += 1
    if verbose:
      print(f'Program {programs_counter:{len_num}}/{num_programs}: code {p}\r',
            end='', file=sys.stderr)

    for_award = None
    r = requests.get(f'http://www.nysed.gov/COMS/RP090/IRPSL3?PROGCD={program.program_code}')
    for line in detail_lines(r.text):
      # Use the first token on a line to determine the type of line, and dispatch to proper handler.
      tokens = line.split()
      token = tokens[0]

      # There is a numeric string (Program Code #.) at the beginning.
      if token.isdecimal():
        # Extract program_code, title, hegis_code, award, institution.
        matches = re.match(r'\s*\d+(.+)(\d{4}\.\d{2})\s+(\S+\s?\S*)\s+(.+)', line)
        if matches is None:
          sys.exit(f'\nUnable to parse program code line for program code {program_code}:\n{line}')
        program_title = fix_title(matches.group(1))
        program_hegis = matches.group(2)
        program_award = matches.group(3).strip()
        program_institution = matches.group(4)
        if debug:
          print(f'{program.program_code}: "{program_title}" {program_hegis}'
                f' {program_award} "{program_institution}"')
        update_program(program, program_institution, institution_name,
                       title=program_title,
                       hegis=program_hegis,
                       award=program_award)

      if token == 'M/A':
        # line_type.multiple_awards
        # Extract title, hegis, award, and institution
        matches = re.match(r'\s*M/A(.+)(\d{4}\.\d{2})\s+(\S+\s?\S*)\s+(.+)', line)
        if matches is None:
          sys.exit(f'\nUnable to parse M/A line for program code {program_code}:\n{line}')
        program_title = fix_title(matches.group(1))
        program_hegis = matches.group(2)
        program_award = matches.group(3).strip()
        program_institution = matches.group(4)
        if debug:
          print(f'{program.program_code}: "{program_title}" {program_hegis}'
                f' {program_award} "{program_institution}"')
        update_program(program, program_institution, institution_name,
                       title=program_title,
                       hegis=program_hegis,
                       award=program_award)

      if token == 'M/I':
        # Multi-institution lines add no new information about a program because multi-award lines
        # already tell what the institution(s) are.
        # But parsing code remains ... “just in case”
        # Extract hegis, award, institution
        #   But there is no hegis if the award is NOT-GRANTING
        if 'NOT-GRANTING' in line:
          program_hegis = None
          program_award = None
          program_institution = line.split('NOT-GRANTING ')[1].strip()
        else:
          matches = re.search(r'(\d{4}.\d{2})\s+(\S+\s?\S*)\s+(.*)', line)
          if matches is None:
            sys.exit(f'\nUnable to parse M/I line for program code {program.program_code}:\n{line}')
          program_hegis = matches.group(1)
          program_award = matches.group(2)
          program_institution = matches.group(3).strip()
        if debug:
          print('M/I:', program_hegis, program_award, program_institution)

      if token == 'FOR':
        # Extract award. The following lines will not be of interest unless the award is in the list
        # for this institution.
        for_award = re.match(r'\s*FOR AWARD\s*--(.*)', line).group(1).strip()
        if for_award not in program.award:
          for_award = None

      if token.startswith('CERTIFICATE') and for_award is not None:
        # Extract certificate tuple {name, type, date} if there is one.
        cert_info = re.sub(r'\s+', ' ', line.split(':')[1].strip())
        if cert_info.startswith('NONE'):
          cert_info = ''
        program.certificate_license = cert_info

      if token == 'PROGRAM' and tokens[1] == 'FINANCIAL' and for_award is not None:
        # Extract three booleans.
        matches = re.search(r'(YES|NO).+(YES|NO).+(YES|NO)', line)
        if matches is None:
          sys.exit('\nUnable to parse eligibility line for program code {}:\n{line}'
                   .format(program.program_code))
        program.tap = matches.group(1) == 'YES'
        program.apts = matches.group(2) == 'YES'
        program.vvta = matches.group(3) == 'YES'

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
        if (program.first_registration_date == 'Unknown'
                or first_date.replace('PRE-', '19') < program.first_registration_date):
          program.first_registration_date = first_date
        if (program.last_registration_date == 'Unknown'
                or last_date > program.last_registration_date):
          program.last_registration_date = last_date
  if verbose:
    print()
  return True


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
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

  institution = args.institution.lower().strip('10')
  if lookup_programs(institution, debug=args.debug, verbose=args.verbose) is not None:
    if args.csv:
      # Generate spreadsheet
      #
      file_name = institution.upper() + '_' + date.today().isoformat() + '.csv'
      with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(Program.headings)
        for p in Program.programs:
          writer.writerow(Program.programs[p].values())
    if args.html:
      print('HTML option not implemented yet', file=sys.stderr)
    if args.update_db:
      print('Database not implemented yet', file=sys.stderr)
  else:
    sys.exit('lookup_programs failed')
