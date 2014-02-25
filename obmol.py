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
n = 0
umdbout = umdb(out)
while notatend:
  n += 1
  sys.stderr.write(str(n)+"\r")
  umdbout.insert_mol(obmol)
  umdbout.insert_molproperty("File source", file)
  obmol = OBMol()
  notatend = obconversion.Read(obmol)
  #if n > 50:
  #  break
umdbout.close()
