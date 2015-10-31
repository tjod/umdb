import sqlite3
import sys
import os
from openbabel import *
from umdb import umdb

# create a umdb from any molecular structure file that openbabel can read

if len(sys.argv) < 2:
  print "usage: obmol.py input_file [output_database]"
  exit()
file = sys.argv[1]
if not os.path.exists(file):
  print "usage: obmol.py input_file [output_database]"
  exit()
fhead, ftail = os.path.split(file)
filename, fileext = os.path.splitext(ftail)
fileext = fileext.replace(".","")
obconversion = OBConversion()
obconversion.SetOptions("-n", obconversion.OUTOPTIONS) # no name
if obconversion.SetInFormat(fileext):
  pass
else:
  print "can't process file type"
  exit()
if len(sys.argv) > 2:
  out = sys.argv[2]
else:
  out = "./" + filename

if os.path.exists(out):
  print out, "file will not be over-written"
  exit()

obmol = OBMol()
notatend = obconversion.ReadFile(obmol, file)
obconversion.SetOutFormat('can')
n = 0
umdbout = umdb(out)
umdbout.create()
while notatend:
  n += 1
  sys.stderr.write(str(n)+"\r")
  #print obmol.GetDimension()
  umdbout.insert_mol(obmol)
  umdbout.insert_molproperty("File source", file)
  if obmol.NumAtoms() > 0 and obmol.NumAtoms() < 150:
	  cansmiles = obconversion.WriteString(obmol,1)
	  umdbout.insert_molproperty("OpenBabel cansmiles", cansmiles)
  obmol = OBMol()
  notatend = obconversion.Read(obmol)
  #if n > 50:
  #  break
umdbout.close()
