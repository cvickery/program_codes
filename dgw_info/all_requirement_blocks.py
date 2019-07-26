#! /usr/local/bin/python3

""" Update requirement block information.

    2019-07-26
    This version works with the CUNY-wide dap_req_block table maintained by OIRA, instead of the
    separate tables used previously.

    The last two columns of the csv are the college in QNS01 format and the date in DD-MMM-YY
    format. (DD-MMM-YY ... really?)
"""

import argparse
from pathlib import Path
import csv
import psycopg2
from psycopg2.extras import NamedTupleCursor
from datetime import datetime, timezone
from collections import namedtuple

# Not in DegreeWorks
# GRD01 | The Graduate Center
# LAW01 | CUNY School of Law
# MED01 | CUNY School of Medicine
# SOJ01 | Graduate School of Journalism
# SPH01 | School of Public Health

# Map DGW college codes to CF college codes
# BB BAR01 | Baruch College
# BC BKL01 | Brooklyn College
# BM BMC01 | Borough of Manhattan CC
# BX BCC01 | Bronx Community College
# CC CTY01 | City College
# HC HTR01 | Hunter College
# HO HOS01 | Hostos Community College
# JJ JJC01 | John Jay College
# KB KCC01 | Kingsborough Community College
# LC LEH01 | Lehman College
# LG LAG01 | LaGuardia Community College
# LU SLU01 | School of Labor & Urban Studies
# ME MEC01 | Medgar Evers College
# NC NCC01 | Guttman Community College
# NY NYT01 | NYC College of Technology
# QB QCC01 | Queensborough Community College
# QC QNS01 | Queens College
# SI CSI01 | College of Staten Island
# SP SPS01 | School of Professional Studies
# YC YRK01 | York College

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', default=False)
args = parser.parse_args()

institution_mappings = {'bb': 'bar',
                        'bc': 'bkl',
                        'bm': 'bmc',
                        'bx': 'bcc',
                        'cc': 'cty',
                        'hc': 'htr',
                        'ho': 'hos',
                        'jj': 'jjc',
                        'kb': 'kcc',
                        'lc': 'leh',
                        'lg': 'lag',
                        'lu': 'slu',
                        'me': 'mec',
                        'nc': 'ncc',
                        'ny': 'nyt',
                        'qb': 'qcc',
                        'qc': 'qns',
                        'si': 'csi',
                        'sp': 'sps',
                        'yc': 'yrk'}
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

# Get list of query files
queries = Path('./queries')
for query in queries.iterdir():
  if query.name.endswith('.csv'):
    with open(query, 'r') as query_file:
      reader = csv.reader(query_file)
      for line in reader:
        print(line[-2:])
#           cursor.execute(f"insert into requirement_blocks values {vals}", (db_record))
#         cursor.execute("""insert into updates values (%s, %s)
#                               on conflict (institution)
#                               do update set last_update = %s
#                        """, (institution, file_time, file_time))
# db.commit()











