import openbabel
import sqlite3
import umdb
import sys

if len(sys.argv) == 1: exit(0)
db = sys.argv[1]
u = umdb.umdb(db)
u.make_mol()
