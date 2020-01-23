from datetime import date
from typing import Dict, Tuple
from pgconnection import PgConnection

known_institutions: Dict[str, Tuple] = dict()

conn = PgConnection()
cursor = conn.cursor()
cursor.execute("select * from nys_institutions")
for row in cursor.fetchall():
  known_institutions[row.id] = (row.institution_id, row.institution_name, row.is_cuny)
conn.close()
