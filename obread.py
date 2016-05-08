import openbabel as ob
import sqlite3
from umdb_openbabel import umdb_openbabel as umdb
import sys

compare = False
db = None
n = 0
ofmt = "can"
for i in range(len(sys.argv)):
	arg = sys.argv[i]
	if arg == "-h":
		print >>sys.stderr, "Usage: obread [-h][-c][-n N] db"
		print >>sys.stderr, "   db is umdb file to read and process into OBMol() and compare/report cansmiles."
		print >>sys.stderr, "   -h: this help."
		print >>sys.stderr, "   -n N: report cansmiles for molecule_id N"
		print >>sys.stderr, "   -o frormat: openbabel output format, e.g. smi, can, mol"
		print >>sys.stderr, "   -c: just compare openbabel cansmiles in db to processed OBMol()s and report mismatches."
		exit()
	elif arg == "-c":
		compare = True
	elif arg == "-n":
		i += 1
		n = int(sys.argv[i])
	elif arg == "-o":
		i += 1
		ofmt = sys.argv[i]
	else:
		db = arg

if db != None:
	u = umdb(db)
	if n > 0:
		mol = u.make_mol(n)
		obc = ob.OBConversion()
		obc.SetOutFormat(ofmt)
		#obc.SetOptions("-n", obc.OUTOPTIONS) # no name
		out = obc.WriteString(mol,1)
		print out
	else:
		u.compare_mols(compare)
	u.close()
