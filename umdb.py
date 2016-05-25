import sqlite3

class umdb:
	"""create umdb file and insert molecule, atoms, bonds, properties"""
	def __init__(self, out):
		"""out is database file name"""
		self.molid = None
		if out:
			self.connection = sqlite3.connect(out)
			self.connection.row_factory = sqlite3.Row
			self.cursor = self.connection.cursor()
			self.cursor.execute('Pragma foreign_keys=ON')
			self.cursor.execute('Pragma defer_foreign_keys=ON')
			#self.cursor.execute('Pragma synchronous=OFF')
			self.cursor.execute('Begin')
			#print 'Begin'

	def create(self):
		"""create the umdb file from sql Create Table statements"""
		script = open('umdb.sql').read()
		self.cursor.executescript(script)

	def commit(self):
		"""commit current changes to database"""
		self.connection.commit()

	def close(self):
		"""commit current changes and close databases"""
		self.connection.commit()
		self.connection.close()
		#print 'End'

	def insert_molecule(self, name, charge=None, multiplicity=None):
		"""insert a new molecule into database"""
		sql = "Insert Into molecule (created, name, charge, multiplicity) Values (datetime('now'), ?,?,?)"
		sqlargs = [name, charge, multiplicity]
		self.cursor.execute(sql, sqlargs)
		self.molid = self.cursor.lastrowid
		self.connection.commit()

	def insert_molproperty(self,  name, value, ns=None):
		"""insert a molecule property into database"""
		sql = "Insert Into property (molecule_id, name, value, ns) Values (?,?,?,?)"
		sqlargs = [self.molid, name, value, ns]
		self.cursor.execute(sql, sqlargs)

	def insert_atomproperty(self, atom_number, name, value, ns=None):
		"""insert an atom property into database"""
		sql = "Insert Into atom_property (molecule_id, atom_number, name, value, ns) Values (?,?,?,?,?)"
		sqlargs = [self.molid, atom_number, name, value, ns]
		self.cursor.execute(sql, sqlargs)

	def insert_bondproperty(self, atoma, atomb, name, value, ns=None):
		"""insert a bond property into database"""
		sql = "Insert Into bond_property (molecule_id, from_atom, to_atom, name, value, ns) Values (?,?,?,?,?,?)"
		bonds = [atoma, atomb]
		bonds.sort()
		sqlargs = [self.molid, bonds[0], bonds[1], name, value, ns]
		self.cursor.execute(sql, sqlargs)

	def insert_atom(self, idx, z=None, symbol=None, name=None, isotope=None, spin=None, charge=None):
		"""insert an atom into the database"""
		atomsql = "Insert Into atom (molecule_id, atom_number, z, symbol, name, a, spin, charge) Values (?,?,?,?,?,?,?,?)"
		sqlargs = [self.molid, idx, z, symbol, name, isotope, spin, charge]
		self.cursor.execute(atomsql, sqlargs)

	def insert_atom_coord(self, idx, x=None, y=None, z=None):
		"""insert an atom's coordinates into the database"""
		coordsql = "Insert Into coord (molecule_id, atom_number, x, y, z) Values (?,?,?,?,?)";
		sqlargs = [self.molid, idx, x, y, z]
		self.cursor.execute(coordsql, sqlargs)

	def insert_bond(self, from_atom, to_atom, bond_order, name=None, ordered=False):
		"""insert a bond into the database"""
		sql = "Insert Or Ignore Into bond (molecule_id, from_atom, to_atom, bond_order, name) Values (?,?,?,?,?)"
		if ordered:
			sqlargs = [self.molid, from_atom, to_atom, bond_order, name]
		else:
			bonds = [from_atom, to_atom]
			bonds.sort()
			sqlargs = [self.molid, bonds[0], bonds[1], bond_order, name]
		self.cursor.execute(sql, sqlargs)

	def insert_residue(self, name, resnum, chain):
		"""insert a residue into the database"""
		ressql = "Insert into residue (molecule_id, name, number, chain) Values (?,?,?,?)"
		sqlargs = [self.molid, name, resnum, chain]
		self.cursor.execute(ressql, sqlargs)

	def insert_residue_atom(self, resnum, chain, idx, name):
		"""insert an atom of a residue into the database"""
		ressql = "Insert into residue_atom (molecule_id, number, chain, atom_number, name) Values (?,?,?,?,?)"
		sqlargs = [self.molid, resnum, chain, idx, name]
		self.cursor.execute(ressql, sqlargs)
		
	def insert_context(self, prefix, suffix):
		"""namespace and name for the context used in properties tables"""
		sql = "Insert Or Ignore Into context (prefix, suffix) Values (?,?)"
		sqlargs = [prefix, suffix]
		self.cursor.execute(sql, sqlargs)

	def symbol_to_z(self):
		"""utility to populate atom z (atomic number) from symbol column"""
		sql = "attach 'element.sqlite' as e"
		self.cursor.execute(sql)
		sql = "update atom set z=(select z from e.element where atom.symbol=element.symbol)"
		self.cursor.execute(sql)

	def z_to_symbol(self):
		"""utility to populate symbol column from atom z (atomic number)"""
		sql = "attach 'element.sqlite' as e"
		self.cursor.execute(sql)
		sql = "update atom set symbol=(select symbol from e.element where atom.z=element.z)"
		self.cursor.execute(sql)

import sys
if __name__ == '__main__':

	if len(sys.argv) == 1:
		exit(0)
	db = sys.argv[1]
	u = umdb(db)
