#! /usr/local/bin/bash
# Update the registered_programs table, which must already exist

# Check that the
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

rm -f csv_files/*

for inst in bar bcc bkl bmc cty csi grd hos htr jjc kcc lag law leh mec \
ncc nyt qcc qns sps yrk
do
  python3 registered_programs.py -cvu $inst
  if [[ $? == 0 ]]
  then # replace any existing spreadsheet(s) for this institution
       rm -f csv_files/`echo $inst|tr a-z A-Z`*csv
       mv `echo $inst|tr a-z A-Z`*csv csv_files
  else exit 1
  fi
done

psql cuny_courses -c "update updates set update_date = '`gdate -I`' \
                        where table_name = 'registered_programs'"
