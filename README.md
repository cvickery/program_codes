# Registered Programs
Academic Program information from NYS Department of Education for registered academic programs.

Scrape the NYS DOE website to extract information for all academic programs registered for any CUNY
college. Includes information on program variants: programs shared across institutions and/or
programs that offer multiple awards.

## Command Line
`python3 registered_programs.py [--help --verbose --csv --html --debug] institution`

Use `--verbose` for progress messages.

The institution is expected to be the CUNYfirst abbreviation for a CUNY college (QNS01 => qns, etc),
but could be any NYSED institution ID number. If the latter case is of use, the code would need to
be updated to show the institution name instead of ID #.

Output can be a CSV file, an HTML table element, and/or entries in a database table.

* Use registered_progams.sql to initialize the db table.
* Excel does not do a good job of opening the CSV file; it mangles text. Import it into Excel
instead.
