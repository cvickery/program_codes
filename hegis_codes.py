#! /usr/local/bin/python3

from datetime import datetime
from AdvancedHTMLParser import AdvancedHTMLParser
import requests
import socket

import psycopg2
from psycopg2.extras import NamedTupleCursor
from sendemail import send_message

# Be sure the NYSED website is accessible before proceeding.
try:
  r = requests.get('http://www.nysed.gov/college-university-evaluation/'
                   'new-york-state-taxonomy-academic-programs-hegis-codes').text
except requests.exceptions.ConnectionError as err:
  send_message([{'name': 'Christopher Vickery', 'email': 'cvickery@qc.cuny.edu'}],
               {'name': 'Transfer App', 'email': 'cvickery@qc.cuny.edu'},
               f'HEGIS Code Update Failed on {socket.gethostname()}',
               f'<p>{err}</p>')
  exit()

db = psycopg2.connect('dbname=cuny_courses')
cursor = db.cursor(cursor_factory=NamedTupleCursor)
cursor.execute('drop table if exists hegis_areas, hegis_codes')
cursor.execute("""
                  create table hegis_areas (
                    id serial primary key,
                    hegis_area text);
                  create table hegis_codes (
                    hegis_code text primary key,
                    area_id integer references hegis_areas,
                    description text
                  );
               """)

parser = AdvancedHTMLParser()
parser.parseStr(r)

area_name = None
area_id = -1
tables = parser.getElementsByTagName('table')
for table in tables:
  assert table.children[0].tagName == 'caption'
  area_name = table.children[0].innerText.strip()
  cursor.execute('insert into hegis_areas values(default, %s) returning id', (area_name, ))
  area_id = cursor.fetchone()[0]
  for row in table.children[2].children:
    assert row.tagName == 'tr'
    hegis_code = row.children[0].innerText.strip()
    description = row.children[1].innerText.strip()
    cursor.execute("""
                      insert into hegis_codes values (%s, %s, %s)
                      on conflict do nothing
                   """, (hegis_code, area_id, description))

changes = parser.getElementsByClassName('pane-node-changed')
update_date = datetime.strptime(changes[0].children[1].innerText.strip(), '%B %d, %Y - %I:%M%p')
cursor.execute(f"update updates set update_date = '{update_date}' where table_name = 'hegis_codes'")
db.commit()
db.close()
