#! /usr/local/bin/bash

# Get latest HEGIS code list from NYS and rebuild the hegis_area and hegis_codes tables.
./hegis_codes.py

# Update the registered_programs table

# Create the table if it does not exist yet.
psql cuny_courses -c "select update_date from updates where table_name = 'registered_programs'"| \
  ack '\d{4}-\d{2}-\d{2}'>/dev/null
if [[ $? == 1 ]]
then echo -n "(Re-)create the registered_programs table ... "
     psql -X -q -d cuny_courses -f registered_programs.sql
     if [[ $? == 0 ]]
     then echo done.
     else echo Failed!
          exit 1
     fi
fi

# Generate/update the database entries and csv file for each college
for inst in bar bcc bkl bmc cty csi grd hos htr jjc kcc lag law leh mec ncc nyt qcc qns sps yrk
do
  python3 registered_programs.py -cvu $inst
  if [[ $? == 0 ]]
  then # replace existing spreadsheet(s) for this institution
       rm -f csv_files/`echo $inst|tr a-z A-Z`*csv
       mv `echo $inst|tr a-z A-Z`*csv csv_files
  else exit 1
  fi
done

# Update the csv file for all institutions
rm -f csv_files/ALL*
path_name="`pwd`/csv_files/ALL_`gdate -I`.csv"
psql cuny_courses -c"copy (select * from registered_programs order by institution, program_code) \
                      to '$path_name' with (header, format csv);"

# Record the date of this update
psql cuny_courses -c "update updates set update_date = '`gdate -I`' \
                        where table_name = 'registered_programs'"
