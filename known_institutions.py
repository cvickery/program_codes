""" Institutions that have academic programs registered with NYS Department of Education.
    Includes all known CUNY colleges plus other institutions that have M/I programs with a CUNY
    institution
    For each institution, the institution id number (as a string), the institution name,
    as spelled on the NYS website, and a boolean to indicate whether it is a CUNY college or not.
"""
known_institutions = {}
known_institutions['bar'] = ('33050', 'CUNY BARUCH COLLEGE', True)
known_institutions['bcc'] = ('37100', 'BRONX COMM COLL', True)
known_institutions['bkl'] = ('33100', 'CUNY BROOKLYN COLL', True)
known_institutions['bmc'] = ('37050', 'BOROUGH MANHATTAN COMM C', True)
known_institutions['cty'] = ('33150', 'CUNY CITY COLLEGE', True)
known_institutions['csi'] = ('33180', 'CUNY COLL STATEN ISLAND', True)
known_institutions['grd'] = ('31050', 'CUNY GRADUATE SCHOOL', True)
known_institutions['hos'] = ('37150', 'HOSTOS COMM COLL', True)
known_institutions['htr'] = ('33250', 'CUNY HUNTER COLLEGE', True)
known_institutions['jjc'] = ('33300', 'CUNY JOHN JAY COLLEGE', True)
known_institutions['kcc'] = ('37250', 'KINGSBOROUGH COMM COLL', True)
known_institutions['lag'] = ('37200', 'LA GUARDIA COMM COLL', True)
known_institutions['law'] = ('31100', 'CUNY LAW SCHOOL AT QUEENS', True)
known_institutions['leh'] = ('33200', 'CUNY LEHMAN COLLEGE', True)
known_institutions['mec'] = ('37280', 'MEDGAR EVERS COLL', True)
known_institutions['ncc'] = ('33350', 'STELLA & CHAS GUTTMAN CC', True)
known_institutions['nyt'] = ('33380', 'NYC COLLEGE OF TECHNOLOGY', True)
known_institutions['qcc'] = ('37350', 'QUEENSBOROUGH COMM COLL', True)
known_institutions['qns'] = ('33400', 'CUNY QUEENS COLLEGE', True)
known_institutions['sps'] = ('31051', 'CUNY SCHOOL OF PROF STUDY', True)
known_institutions['yrk'] = ('33500', 'CUNY YORK COLLEGE', True)
known_institutions['bst'] = ('40450', 'BANK STREET COLLEGE OF ED', False)
known_institutions['bls'] = ('40900', 'BROOKLYN LAW SCHOOL', False)
