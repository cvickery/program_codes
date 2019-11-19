#! /usr/local/bin/python3
""" Filter to put \r\n between lines and just \n within fields of a csv file.
    While at it, filter out ASCII codes in the range 0x0E and 0x1f
"""

import sys
import argparse

CR = chr(0x0D)
LF = chr(0x0A)

blk = '\x1b[30m'
red = '\x1b[31m'
grn = '\x1b[32m'

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--delimiter', default=',')
parser.add_argument('-q', '--quotechar', default='"')
args = parser.parse_args()

delimiter = args.delimiter
quotechar = args.quotechar

in_field = False
last_char = None
with sys.stdin as infile:
  with sys.stdout as outfile:
    while True:
      ch = infile.read(1)
      if not ch:
        exit()
      if ord(ch) < 0x20 and ord(ch) > 0x0d:
        continue
      if ch == quotechar:
        in_field = not in_field
        # if in_field:
        #   outfile.write(grn)
        # else:
        #   outfile.write(blk)
      if ch == LF and last_char != CR and not in_field:
        # print(f' CR', file=sys.stderr, end='')
        outfile.write(CR)
        last_char = CR
      if ch == CR and in_field:
        continue
      outfile.write(ch)
      last_char = ch
      # print(f' {ch}', file=sys.stderr, end='')
print()
