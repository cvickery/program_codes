#! /usr/local/bin/bash
for inst in bar bcc bkl bmc cty csi grd hos htr jjc kcc lag law leh mec \
ncc nyt qcc qns sps yrk
do
  python3 registered_programs.py -cvu $inst
  mv `echo $inst|tr a-z A-Z`*csv csv_files
done
psql cuny_courses -c "update updates set update_date = '`date -I`' \
                     where table_name = 'registered_programs'"
