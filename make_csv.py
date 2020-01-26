#! /usr/local/bin/python3
""" Generate a CSV file from the csv column of registered_programs.
    Next step will be to generate the file in memory and to provide an html link element for
    downloading it.
"""
import io
import sys
import csv
import json

from pgconnection import PgConnection

headings = ['Program Code',
            'Registration Office',
            'Institution',
            'Program Title',
            'Formats',
            'HEGIS',
            'Award',
            'CIP Code',
            'CUNY Program(s)',
            'Certificate or License',
            'Accreditation',
            'First Reg. Date',
            'Latest Reg. Action',
            'TAP',
            'APTS',
            'VVTA']

conn = PgConnection()
cursor = conn.cursor()
cursor.execute("""select csv
                    from registered_programs
                   where institution~*'qns'""")
with io.StringIO('') as csvfile:
  writer = csv.writer(csvfile)
  writer.writerow(headings)
  for row in cursor.fetchall():
    writer.writerow(json.loads(row.csv))
  gen = csvfile.getvalue()
print(gen)
conn.close()
