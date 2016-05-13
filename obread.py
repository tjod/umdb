import openbabel as ob
#import sqlite3
from umdb_openbabel import umdb_openbabel as umdb
import sys

compare = False
db = None
n = 0
ofmt = "can"
line_numbers = False
molnames = False
for i in range(len(sys.argv)):
	arg = sys.argv[i]
	if arg == "-h":
		print >>sys.stderr, "Usage: obread [-h][-c][-n N] db"
		print >>sys.stderr, "   db is umdb file to read and process into OBMol() and compare/report cansmiles."
		print >>sys.stderr, "   -h: this help."
		print >>sys.stderr, "   -i N: report cansmiles for molecule_id N"
		print >>sys.stderr, "   -o format: openbabel output format, e.g. smi, can, mol"
		print >>sys.stderr, "   -l: include line numbers in output"
		print >>sys.stderr, "   -n: include molecule names in output"
		print >>sys.stderr, "   -c: just compare openbabel cansmiles in db to processed OBMol()s and report mismatches; obviates -i -l -n -o"
		exit()
	elif arg == "-c":
		compare = True
	elif arg == "-n":
		molnames = True
	elif arg == "-l":
		line_numbers = True
	elif arg == "-i":
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
		u.compare_mols(compare, fmt=ofmt, line_numbers=line_numbers, molnames=molnames)
	u.close()
