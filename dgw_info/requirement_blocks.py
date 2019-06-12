""" Update requirement block information.
"""

from pathlib import Path
import csv
import psycopg2
from psycopg2.extras import NamedTupleCursor
from datetime import datetime, timezone

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

db = psycopg2.connect('dbname=cuny_programs')
cursor = db.cursor(cursor_factory=NamedTupleCursor)

# Get list of query files
queries = Path('./queries')
for query in queries.iterdir():
  if query.name.endswith('.csv'):
    if query.name[0:2] in institution_mappings.keys():
      institution = institution_mappings[query.name[0:2]]
      file_time = datetime.fromtimestamp(query.stat().st_mtime, tz=timezone.utc)
      cursor.execute("select last_update from updates where institution = %s", (institution, ))
      assert cursor.rowcount < 2, f'Error: multiple updates for {query.name}'
      if cursor.rowcount == 1:
        last_update = cursor.fetchone().last_update
      if cursor.rowcount == 0 or last_update < file_time:
        print('AND NOW DO SOMETHING INTERESTING')
        cursor.execute("""insert into updates values (%s, %s)
                              on conflict (institution)
                              do update set last_update = %s
                       """, (institution, file_time, file_time))
db.commit()











