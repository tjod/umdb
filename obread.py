import openbabel as ob
import sqlite3
from umdb_openbabel import umdb_openbabel as umdb
import sys

compare = False
db = None
n = 0
for i in range(len(sys.argv)):
	arg = sys.argv[i]
	if arg == "-h":
		print >>sys.stderr, "Usage: obread [-h][-c][-n N] db"
		print >>sys.stderr, "   db is umdb file to read and process into OBMol() and compare/report cansmiles."
		print >>sys.stderr, "   -h: this help."
		print >>sys.stderr, "   -n N: report cansmiles for molecule_id N"
		print >>sys.stderr, "   -c: just compare openbabel cansmiles in db to processed OBMol()s and report mismatches."
		exit()
	elif arg == "-c":
		compare = True
	elif arg == "-n":
		i += 1
		n = int(sys.argv[i])
	else:
		db = arg

if db != None:
	u = umdb(db)
	if n > 0:
		mol = u.make_mol(n)
		obc = ob.OBConversion()
		obc.SetOutFormat('can')
		#obc.SetOptions("-n", obc.OUTOPTIONS) # no name
		cansmiles = obc.WriteString(mol,1)
		print cansmiles
	else:
		u.compare_mols(compare)
	u.close()
