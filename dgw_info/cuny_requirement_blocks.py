#! /usr/local/bin/python3

""" Insert or update the cuny_programs.requirement_blocks table from a cuny-wide extract (includes
    an institution column in addition to the DegreeWorks DAP_REQ_BLOCK columns.)

    2019-11-10
    Accept requirement block exports in either csv or xml format.

    2019-07-26
    This version works with the CUNY-wide dap_req_block table maintained by OIRA, instead of the
    separate tables used in requirement_blocks.py version (which supports only csv input).

    CUNY Institutions Not In DegreeWorks
    GRD01 | The Graduate Center
    LAW01 | CUNY School of Law
    MED01 | CUNY School of Medicine
    SOJ01 | Graduate School of Journalism
    SPH01 | School of Public Health

    Map DGW college codes to CF college codes
    BB BAR01 | Baruch College
    BC BKL01 | Brooklyn College
    BM BMC01 | Borough of Manhattan CC
    BX BCC01 | Bronx Community College
    CC CTY01 | City College
    HC HTR01 | Hunter College
    HO HOS01 | Hostos Community College
    JJ JJC01 | John Jay College
    KB KCC01 | Kingsborough Community College
    LC LEH01 | Lehman College
    LG LAG01 | LaGuardia Community College
    LU SLU01 | School of Labor & Urban Studies
    ME MEC01 | Medgar Evers College
    NC NCC01 | Guttman Community College
    NY NYT01 | NYC College of Technology
    QB QCC01 | Queensborough Community College
    QC QNS01 | Queens College
    SI CSI01 | College of Staten Island
    SP SPS01 | School of Professional Studies
    YC YRK01 | York College
"""

import re
import sys
import csv
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import namedtuple
from xml.etree.ElementTree import parse

import psycopg2
from psycopg2.extras import NamedTupleCursor

csv.field_size_limit(sys.maxsize)

trans_dict = dict()
for c in range(14, 31):
  trans_dict[c] = None

cruft_table = str.maketrans(trans_dict)


def decruft(block):
  """ Remove chars in the range 0x0e through 0x1f and return the block otherwise unchanged.
      This is the same thing strip_file does, which has to be run before this program for xml
      files. But for csv files where strip_files wasn't run, this makes the text cleaner, avoiding
      possible parsing problems.
  """
  return block.translate(cruft_table)


def csv_generator(file):
  """ Generate rows from a csv export of OIRA’s DAP_REQ_BLOCK table.
  """
  cols = None
  with open(file, newline='') as query_file:
    reader = csv.reader(query_file,
                        delimiter=args.delimiter,
                        quotechar=args.quotechar)
    for line in reader:
      if cols is None:
        cols = [col.lower().replace(' ', '_') for col in line]
        Row = namedtuple('Row', cols)
      else:
        try:
          row = Row._make(line)
          yield row
        except TypeError as type_error:
          print(f'{type_error}: |{line}|', file=sys.stderr)


def xml_generator(file):
  """ Generate rows from an xml export of OIRA’s DAP_REQ_BLOCK table.
  """
  try:
    tree = parse(file)
  except xml.etree.ElementTree.ParseError as pe:
    sys.exit(pe)

  Row = None
  for record in tree.findall("ROW"):
    cols = record.findall('COLUMN')
    line = [col.text for col in cols]
    if Row is None:
      # array = [col.attrib['NAME'].lower() for col in cols]
      Row = namedtuple('Row', [col.attrib['NAME'].lower() for col in cols])
    row = Row._make(line)
    yield row


parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', default=False)
parser.add_argument('-v', '--verbose', action='store_true', default=False)
parser.add_argument('-f', '--file', default='./downloads/dap_req_block.csv')
parser.add_argument('-de', '--delimiter', default=',')
parser.add_argument('-q', '--quotechar', default='"')
args = parser.parse_args()

db_cols = ['institution',
           'requirement_id',
           'block_type',
           'block_value',
           'title',
           'period_start',
           'period_stop',
           'major1',
           'major2',
           'concentration',
           'minor',
           'requirement_text']
vals = '%s, ' * len(db_cols)
vals = '(' + vals.strip(', ') + ')'

DB_Record = namedtuple('DB_Record', db_cols)

db = psycopg2.connect('dbname=cuny_curriculum')
cursor = db.cursor(cursor_factory=NamedTupleCursor)

# Dict of rows by institution
institutions = {}
Institution = namedtuple('Institution', 'load_date rows')

file = Path(args.file)
if not file.exists():
  sys.exit(f'File not found: {file}')

if file.suffix.lower() == '.xml':
  generator = xml_generator
elif file.suffix.lower() == '.csv':
  generator = csv_generator
else:
  sys.exit(f'Unsupported file type: {file.suffix}')

# Gather all the rows for all the institutions
for row in generator(file):
  institution = row.institution.upper()

  # Integrity check: all rows for an institution must have the same load date.
  load_date = row.irdw_load_date[0:10]
  if institution not in institutions.keys():
    institutions[institution] = Institution._make([load_date, []])
  assert load_date == institutions[institution].load_date, \
      f'{load_date} is not {institutions[institution].load_date} for {institution}'

  institutions[institution].rows.append(row)

# Create the requirement_blocks table if it doesn’t already exist
cursor.execute("""create table if not exists requirement_blocks (
                  institution text,
                  requirement_id text,
                  block_type text,
                  block_value text,
                  title text,
                  period_start text,
                  period_stop text,
                  major1 text,
                  major2 text,
                  concentration text,
                  minor text,
                  requirement_text text,
                  primary key (institution, requirement_id))""")

# Process the rows from the csv or xml file, institution by institution
for institution in institutions.keys():
  # Delete what was already available for this institution
  cursor.execute(f'delete from requirement_blocks where institution = %s',
                 (institution, ))
  if args.verbose:
    num_blocks = cursor.rowcount
    suffix = '' if num_blocks == 1 else 's'
    print(f'Replacing {num_blocks:,} existing blocks for {institution}')

  load_date = institutions[institution].load_date
  # Desired date format: YYYY-MM-DD
  if re.match(r'^\d{4}-\d{2}-\d{2}$', load_date):
    pass
  # Alternate format: DD-MMM-YY
  elif re.match(r'\d{2}-[a-z]{3}-\d{2}', load_date, re.I):
    load_date = datetime.strptime(load_date, '%d-%b-%y').strftime('%Y-%m-%d')
  else:
    sys.exit(f'Unrecognized load date format: {load_date}')

  num_records = len(institutions[institution].rows)
  suffix = '' if num_records == 1 else 's'
  if args.verbose:
    print(f'Processing {num_records:,} record{suffix} dated {load_date} '
          f'from {file} for {institution}')

  for row in institutions[institution].rows:
    db_record = DB_Record._make([institution,
                                 row.requirement_id,
                                 row.block_type,
                                 row.block_value,
                                 row.title,
                                 row.period_start,
                                 row.period_stop,
                                 row.major1,
                                 row.major2,
                                 row.concentration,
                                 row.minor,
                                 decruft(row.requirement_text.replace('\t', ' '))])
    set_clause = 'set '
    set_clause += ', '.join([f'{col} = %s' for col in db_cols])
    cursor.execute(f"""update requirement_blocks {set_clause}
                       where requirement_id = %s and institution = %s;
                       insert into requirement_blocks values {vals}
                       on conflict do nothing
                    """, (db_record + (row.requirement_id, institution) + db_record))

cursor.execute(f"""update updates
                      set update_date = '{load_date}'
                    where table_name = 'requirement_blocks'""")
db.commit()
db.close()

# Archive the file just processed
file.rename(f'/Users/vickery/CUNY_Programs/dgw_info/archives/'
            f'{file.stem}_{load_date}{file.suffix}')
