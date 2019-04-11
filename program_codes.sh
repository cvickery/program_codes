#! /usr/local/bin/bash

# Get information about all academic programs for Queens College from the NYS Department of
# Education, using web requests.
#
# The first request simulates submitting a form to get information for all programs; a sed
# script extracts all the program codes, which go to a series of web requests to extract
# the details about each program.
#
# Christopher Vickery
# January 2016

start_time=`date +%s`
ymd=`date +%Y-%m-%d`
(( n = 0 ))
program_codes=`curl --data "SEARCHES=1&instid=334000" http://www.nysed.gov/coms/rp090/IRPS2A 2>/dev/null |\
   sed -n 's/.*PROGCD=\([0-9]*\).*/\1/p'`
num_codes=`echo $program_codes|wc -w`
echo "There are $num_codes program codes"
for program_code in $program_codes
do
 (( n = n + 1 ))
  echo "Retrieving info for program code $n/$num_codes: $program_code"
#  curl http://www.nysed.gov/COMS/RP090/IRPSL3?PROGCD=$program_code >> program_codes.raw
 curl http://www.nysed.gov/COMS/RP090/IRPSL3?PROGCD=$program_code 2>/dev/null | \
 ack "$program_code |FOR AWARD|PROGRAM FIN|PROGRAM PRO|CERTIFICATE|QUEENS" | \
 sed 's/<H4><PRE>//' >> program_codes.out
done
echo "Retrieved info for $n program codes"

# Generate spreadsheet from the program_codes.out file
#./program_codes.py

# Datestamp today’s files
# mv program_codes.out program_codes.${ymd}.out
# mv program_codes.xlsx program_codes.${ymd}.xlsx
 end_time=`date +%s`

 echo "Completed in $(( $end_time - $start_time )) seconds."
