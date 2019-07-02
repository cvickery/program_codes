#! /usr/local/bin/python3
""" Scrape the current list of program formats from the NYS DOE website.
    Result is the program_formats table.

    __author__ = 'Christopher Vickery'
    __version__ = 'July 2019'

"""
import sys
import re
import argparse

from datetime import datetime

import requests
from lxml.html import document_fromstring
import cssselect

import psycopg2
from psycopg2.extras import NamedTupleCursor

conn = psycopg2.connect('dbname=cuny_courses')
cursor = conn.cursor(cursor_factory=NamedTupleCursor)
cursor.execute("""
  drop table if exists program_formats;
  create table program_formats (
  name text primary key,
  description text,
  abbr text default '');
  """)

r = requests.get('http://www.nysed.gov/college-university-evaluation/format-definitions')
html_document = document_fromstring(r.content)
for p in html_document.cssselect('.field__items p'):
  name, description = p.text_content().split(':', 1)
  q = f'insert into program_formats values (%s, %s)'
  cursor.execute(q, (name.strip(), description.strip()))

update_div = html_document.cssselect('.pane-node-changed div + div')
update_date = datetime.strptime(update_div[0].text_content().strip(), '%B %d, %Y - %I:%M%p')
cursor.execute("update updates set update_date = %s where table_name = 'program_formats'",
               (update_date,))
conn.commit()
conn.close()
