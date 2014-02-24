import sqlite3
import sys
import os
from openbabel import *
from umdb import umdb

if len(sys.argv) < 3:
  print "usage: obmol.py input_file output_file"
  exit()
file = sys.argv[1]
if not os.path.exists(file):
  print "usage: obmol.py input_file output_file"
  exit()
filename, fileext = os.path.splitext(file)
fileext = fileext.replace(".","")
obconversion = OBConversion()
if obconversion.SetInFormat(fileext):
  pass
else:
  print "can't process file type"
  exit()
out = sys.argv[2]

obmol = OBMol()
notatend = obconversion.ReadFile(obmol, file)
while notatend:
  umdb(out).insert_mol(obmol)
  obmol = OBMol()
  notatend = obconversion.Read(obmol)
