#! /usr/local/bin/bash

# Get latest HEGIS code list from NYS and rebuild the hegis_area and hegis_codes tables.
./hegis_codes.py

# Get the latest list of NYS institutions
./nys_institutions.py
if [[ $? != 0 ]]
then echo 'Update NYS Institutions Failed!'
     exit 1
fi

# Update the registered_programs table

# Create the table if it does not exist yet.
psql cuny_courses -tXc \
"select update_date from updates where table_name = 'registered_programs'" | pbcopy
update_date=`pbpaste|tr -d ' '`
if [[ $update_date == '' ]]
then echo -n "(Re-)create the registered_programs table ... "
     psql -qXd cuny_courses -f registered_programs.sql
else echo -n "Archive registered_programs table $update_date ... "
     pg_dump cuny_courses -t registered_programs > "./archives/registered_programs_${update_date}.sql"
fi
if [[ $? == 0 ]]
then echo done.
else echo Failed!
    exit 1
fi

# Generate/update the database entries and csv file for each college
for inst in bar bcc bkl bmc cty csi grd hos htr jjc kcc lag law leh mec ncc nyt qcc qns sps yrk
do
  python3 registered_programs.py -vu $inst
  if [[ $? != 0 ]]
  then  echo "Update failed for $inst"
        exit 1
  fi
done

# Generate the csv file for all institutions
rm -f csv_files/ALL*
path_name="`pwd`/csv_files/ALL_`gdate -I`.csv"
psql cuny_courses -c"copy (select * from registered_programs order by institution, program_code) \
                      to '$path_name' with (header, format csv);"

# Record the date of this update
psql cuny_courses -c "update updates set update_date = '`gdate -I`' \
                        where table_name = 'registered_programs'"

# Recreate the requirements_blocks table, using the latest available csv file from OIRA.
(
  cd ./dgw_info
  if [[ ! -e downloads/dap_req_block.csv ]]
  then  # Find the latest file in the archives folder
        shopt -s nullglob
        all=(./archives/dap*)
        n=$(( ${#all[@]} - 1 ))
        latest=${all[$n]}
        cp $latest ./downloads/dap_req_block.csv
        echo "No new dap_req_block.csv in downloads. Using $latest."
  fi
  ./cuny_requirement_blocks.py
)
