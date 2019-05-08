#! /usr/local/bin/bash
# Re-initialize and populate the registered_programs table.

psql cuny_courses < registered_programs.sql

rm csv_files/*

for inst in bar bcc bkl bmc cty csi grd hos htr jjc kcc lag law leh mec \
ncc nyt qcc qns sps yrk
do
  python3 registered_programs.py -cvu $inst
  mv `echo $inst|tr a-z A-Z`*csv csv_files
done

psql cuny_courses -c "update updates set update_date = '`gdate -I`' \
                     where table_name = 'registered_programs'"
