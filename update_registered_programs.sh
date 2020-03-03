#! /usr/local/bin/bash

echo Start update_registered_programs.py at `date`
export PYTHONPATH=/Users/vickery/Transfer_App/

echo -n 'Get latest dap_req_block ...'
# Download new dap_req_block.csv if there is one from OIRA
export LFTP_PASSWORD=`cat /Users/vickery/.lftpwd`
if [[ `hostname` != 'cvlaptop.local' && `hostname` != 'cvhome.local' ]]
then /usr/local/bin/lftp -f ./getcunyrc
fi
echo done

# Copy IPEDS CIP codes to the cip_codes table.
echo -n 'Recreate CIP Codes table ... '
./cip_codes.py
if [[ $? != 0 ]]
then echo 'FAILED!'
     exit 1
else echo 'done.'
fi

# Get latest HEGIS code list from NYS and rebuild the hegis_area and hegis_codes tables.
echo -n 'Update NYS HEGIS Codes ... '
./hegis_codes.py
if [[ $? != 0 ]]
then echo 'FAILED!'
     exit 1
else echo 'done.'
fi

# Get the latest list of NYS institutions
echo -n 'Update NYS Institutions ... '
./nys_institutions.py
if [[ $? != 0 ]]
then echo 'FAILED!'
     exit 1
else echo 'done.'
fi

# Update the registered_programs table

# Create the table if it does not exist yet.
psql cuny_curriculum -tXc \
"select update_date from updates where table_name = 'registered_programs'" | pbcopy
update_date=`pbpaste|tr -d ' '`
if [[ $update_date == '' ]]
then echo -n "(Re-)create the registered_programs table ... "
     psql -qXd cuny_curriculum -f registered_programs.sql
else echo -n "Archive registered_programs table $update_date ... "
     pg_dump cuny_curriculum -t registered_programs > "./archives/registered_programs_${update_date}.sql"
fi
if [[ $? == 0 ]]
then echo done.
else echo Failed!
    exit 1
fi

# Generate/update the registered_programs table for all colleges
for inst in bar bcc bkl bmc cty csi grd hos htr jjc kcc lag law leh mec ncc nyt qcc qns sps yrk
do
  python3 registered_programs.py -vu $inst
  if [[ $? != 0 ]]
  then  echo "Update failed for $inst"
        exit 1
  fi
done

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

# Generate the HTML and CSV table rows for registered programs (including links to the requirement
# blocks)
echo -n 'Generate HTML and CSV row elements for registered programs ...'
./generate_html.py
if [[ $? != 0 ]]
then echo 'FAILED!'
     exit 1
else echo 'done.'
fi

# Record the date of this update
psql cuny_curriculum -Xqc "update updates set update_date = '`gdate -I`' \
                        where table_name = 'registered_programs'"

echo End update_registered_programs.py at `date`
