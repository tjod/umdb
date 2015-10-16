import sqlite3
import sys
import os
from openbabel import *
from umdb import umdb

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
n = 0
umdbout = umdb(out)
umdbout.create()
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
