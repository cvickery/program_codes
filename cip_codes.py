#! /usr/local/bin/python3

import csv
from pathlib import Path
from collections import namedtuple
from pgconnection import PgConnection

conn = PgConnection()
cursor = conn.cursor()
cursor.execute('drop table if exists cip_codes')
cursor.execute('create table cip_codes (cip_code text primary key, cip_title text)')

code_files = sorted(Path.glob(Path('ipeds'), '*.csv'))
cols = None
with open(code_files[-1]) as code_file:
  reader = csv.reader(code_file)
  for line in reader:
    if cols is None:
      cols = [col.lower().replace(' ', '_') for col in line]
      Row = namedtuple('Row', cols)
    else:
      row = Row._make(line)
      cursor.execute('insert into cip_codes values (%s, %s)',
                     (row.cipcode.strip('="'), row.ciptitle))
conn.commit()
conn.close()
