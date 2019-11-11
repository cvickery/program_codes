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


def csv_generator(file):
  """ Generate rows from a csv export of OIRA’s DAP_REQ_BLOCK table.
  """
  cols = None
  with open(file, 'r') as query_file:
    reader = csv.reader(query_file)
    for line in reader:
      if cols is None:
        cols = [col.lower().replace(' ', '_') for col in line]
        Row = namedtuple('Row', cols)
      else:
        row = Row._make(line)
        yield row


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
parser.add_argument('-f', '--file', default='./queries/dap_req_block.xml')
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

db = psycopg2.connect('dbname=cuny_programs')
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
  institution = row.institution.lower().strip('10')

  # Integrity check: all rows for an institution must have the same load date.
  load_date = row.irdw_load_date[0:10]
  if institution not in institutions.keys():
    institutions[institution] = Institution._make([load_date, []])
  assert load_date == institutions[institution].load_date, \
      f'{load_date} is not {institutions[institution].load_date} for {institution}'

  institutions[institution].rows.append(row)

# Process the rows, institution by institution
for institution in institutions.keys():
  # Report what was already available for this institution
  if args.verbose:
    last_update = 'never'
    cursor.execute("select * from updates where institution = %s", (institution, ))
    if cursor.rowcount == 1:
      last_update = str(cursor.fetchone().last_update)
    cursor.execute(f'select count(*) from requirement_blocks where institution = %s',
                   (institution, ))
    num_blocks = int(cursor.fetchone()[0])
    suffix = '' if num_blocks == 1 else 's'
    print(f'Found {num_blocks:,} existing blocks for {institution}, '
          f'last updated {last_update}')

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

  cursor.execute("""insert into updates values (%s, %s)
                        on conflict (institution)
                        do update set last_update = %s
                 """, (institution, load_date, load_date))

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
                                 row.requirement_text])
    set_clause = 'set '
    set_clause += ', '.join([f'{col} = %s' for col in db_cols])
    cursor.execute(f"""update requirement_blocks {set_clause}
                       where requirement_id = %s and institution = %s;
                       insert into requirement_blocks values {vals}
                       on conflict do nothing
                    """, (db_record + (row.requirement_id, institution) + db_record))

db.commit()
db.close()

# Archive the file just processed
file.rename(f'./query_archive/{file.stem}_{load_date}{file.suffix}')
