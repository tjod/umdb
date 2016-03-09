import sqlite3
from openbabel import *
import json

class umdb:
	def __init__(self, out):
		self.molid = 0
		# workaround
		OBStereo.NoRef = 4294967295
		OBStereo.ImplicitRef = 4294967294
		self.ElementTable = OBElementTable()
		if out:
			self.connection = sqlite3.connect(out)
			self.connection.row_factory = sqlite3.Row
			self.cursor = self.connection.cursor()
			self.cursor.execute('Pragma foreign_keys=ON')
			self.cursor.execute('Pragma defer_foreign_keys=ON')
			#self.cursor.execute('Pragma synchronous=OFF')
			self.cursor.execute('Begin')
			print 'Begin'

	def create(self):
		script = open('umdb.sql').read()
		self.cursor.executescript(script)

#	def get_atom_stereo(self, facade, obmol, atom):
#		f = facade.GetTetrahedralStereo(atom.GetId())
#		cfg = f.GetConfig()
#		assert cfg.center == atom.GetId()
#		return self.stereoCfgToDict(cfg, obmol)

	def stereoCfgToDict(self, cfg, obmol):
		stereo = dict()
		stereo['specified'] = cfg.specified
		stereo['center'] = obmol.GetAtomById(cfg.center).GetIdx()
		stereo['winding'] = 'Clockwise' if cfg.winding == OBStereo.Clockwise \
				else 'AntiClockwise'
		stereo['view'] = 'From' if cfg.view == OBStereo.ViewFrom \
				else 'Towards'
		stereo['look'] = 'None' if cfg.from_or_towards == OBStereo.NoRef \
				else 'Implicit' if cfg.from_or_towards == OBStereo.ImplicitRef \
				else obmol.GetAtomById(cfg.from_or_towards).GetIdx()
		stereo['refs'] = ['None' if r == OBStereo.NoRef \
				else 'Implicit' if r == OBStereo.ImplicitRef \
				else obmol.GetAtomById(r).GetIdx() for r in cfg.refs]
		return stereo

	def cistransCfgToDict(self, cfg, obmol):
		cistrans = dict()
		cistrans['specified'] = cfg.specified
		cistrans['begin'] = obmol.GetAtomById(cfg.begin).GetIdx()
		cistrans['end']   = obmol.GetAtomById(cfg.end).GetIdx()
		cistrans['shape'] = 'U' if cfg.shape == OBStereo.ShapeU \
				else 'Z' if cfg.shape == OBStereo.ShapeZ \
				else '4'
		cistrans['refs'] = ['None' if r == OBStereo.NoRef \
				else 'Implicit' if r == OBStereo.ImplicitRef \
				else obmol.GetAtomById(r).GetIdx() for r in cfg.refs]
		return cistrans

	def insert_mol(self, obmol, bonds=True):
		sqlargs = [obmol.GetTitle()]
		sql = "Insert into molecule (created, name) Values (datetime('now'), ?)"
		self.cursor.execute(sql, sqlargs)
		self.molid = self.cursor.lastrowid
		#self.insert_molproperties(obmol)
		self.insert_residues(obmol)
		self.insert_atoms(obmol)
		self.insert_atomproperties(obmol)
		if bonds:
			self.insert_bonds(obmol)
			self.insert_bondproperties(obmol)
		self.connection.commit()

	def insert_molproperty(self, name, value):
		sql = "Insert Into property (molecule_id, name, value) Values (?,?,?)"
		sqlargs = [self.molid, name, value]
		self.cursor.execute(sql, sqlargs)

	def insert_atomproperty(self, atom_number, name, value):
		sql = "Insert Into atom_property (molecule_id, atom_number, name, value) Values (?,?,?,?)"
		sqlargs = [self.molid, atom_number, name, value]
		self.cursor.execute(sql, sqlargs)

	def insert_bondproperty(self, atoma, atomb, name, value):
		sql = "Insert into bond_property (molecule_id, from_atom, to_atom, name, value) Values (?,?,?,?,?)"
		bonds = [atoma, atomb]
		bonds.sort()
		sqlargs = [self.molid, bonds[0], bonds[1], name, value]
		self.cursor.execute(sql, sqlargs)


	def close(self):
		self.connection.commit()
		self.connection.close()
		print 'End'

	def insert_atomproperties(self, obmol):
		#sql = "Insert into atom_property (molecule_id, atom_number, name, value) Values (?,?,?,?)"
		for atom in OBMolAtomIter(obmol):
		  for p in atom.GetAllData(0):
			 insert_atomproperty(atom.GetIdx(), p.GetAttribute(), p.GetValue())

	def cansmiles_atom_order(self, obmol):
		for p in obmol.GetData():
			if p.GetDataType() == PairData:
				if p.GetAttribute() == 'SMILES Atom Order':
					return map(int, p.GetValue().split())

	def insert_molproperties(self, obmol):
		for p in obmol.GetData():
			if p.GetDataType() == PairData:
				if p.GetAttribute() == 'OpenBabel Symmetry Classes': continue
				self.insert_molproperty(p.GetAttribute(), p.GetValue())
			elif p.GetDataType() == StereoData:
				ts = toTetrahedralStereo(p)
				if ts.IsValid():
					cfg = ts.GetConfig()
					#print 'stereo',self.stereoCfgToDict(cfg, obmol)
					if cfg.specified:
						self.insert_molproperty('OBTetrahedralStereo', json.dumps(self.stereoCfgToDict(cfg, obmol)))
				else:
					ct = toCisTransStereo(p)
					cfg = ct.GetConfig()
					#print 'cistrans',self.cistransCfgToDict(cfg, obmol)
					if cfg.specified:
						self.insert_molproperty('OBCisTransStereo', json.dumps(self.cistransCfgToDict(cfg, obmol)))

	def insert_residues(self, obmol):
		ressql = "Insert into residue (molecule_id, name, number, chain) Values (?,?,?,?)"
		for res in OBResidueIter(obmol):
			sqlargs = [self.molid, res.GetName(), res.GetNum(), res.GetChain()]
			self.cursor.execute(ressql, sqlargs)

	def insert_atoms(self, obmol):
		atomsql = "Insert into atom (molecule_id, atom_number, z, symbol, name, a, spin, charge) Values (?,?,?,?,?,?,?,?)"
		coordsql = "Insert into coord (molecule_id, atom_number, x, y, z) Values (?,?,?,?,?)";
		ressql = "Insert into residue_atom (molecule_id, number, chain, atom_number, name) Values (?,?,?,?,?)"
		#facade = OBStereoFacade(obmol);
		for atom in OBMolAtomIter(obmol):
			isotope = int(atom.GetIsotope())
			charge = int(atom.GetFormalCharge())
			spin = int(atom.GetSpinMultiplicity())
			name = atom.GetTitle()
			if isotope == 0:
				isotope = None #isotope = int(OBIsotopeTable().GetExactMass (atom.GetAtomicNum()))
			if spin == 0:
				spin = None
			sqlargs = [self.molid, atom.GetIdx(), atom.GetAtomicNum(), self.ElementTable.GetSymbol(atom.GetAtomicNum()), name, isotope, spin, charge]
			self.cursor.execute(atomsql, sqlargs)
			# store atom coords
			if obmol.GetDimension() > 0:
				sqlargs = [self.molid, atom.GetIdx(), atom.x(), atom.y(), atom.z()]
				self.cursor.execute(coordsql, sqlargs)
			# store atom name in residue (pdb)
			if atom.HasResidue():
				res = atom.GetResidue()
				atom_name = res.GetAtomID(atom)
				sqlargs = [self.molid,  res.GetNum(), res.GetChain(), atom.GetIdx(), atom_name]
				self.cursor.execute(ressql, sqlargs)
			atype = atom.GetType()
			if atype:
				self.insert_atomproperty(atom.GetIdx(), 'OBType', atype)
			partial = atom.GetPartialCharge()
			#if partial:
				#self.insert_atomproperty(atom.GetIdx(), 'PartialCharge', partial)

			# goes into molecule property now
			#if facade.HasTetrahedralStereo(atom.GetId()):
			#	stereo = self.get_atom_stereo(facade, obmol, atom)
			#	self.insert_property(atom.GetIdx(), 'OBStereo', json.dumps(stereo))

	def insert_bonds(self, obmol):
		sql = "Insert into bond (molecule_id, from_atom, to_atom, bond_order) Values (?,?,?,?)"
		for bond in OBMolBondIter(obmol):
			bonds = [bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()]
			bonds.sort()
			sqlargs = [self.molid, bonds[0], bonds[1], bond.GetBondOrder()]
			self.cursor.execute(sql, sqlargs)

	def insert_bondproperties(self, obmol):
		for bond in OBMolBondIter(obmol):
			for p in bond.GetData():
				if toPairData(p).GetDataType() == PairData:
					self.insert_bondproperty(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx(), p.GetAttribute(), p.GetValue())

	def make_atoms(self, imol, mol):
		#sql = "Select molecule_id, atom_number, z, symbol, name, a, spin, charge From atom Where molecule_id = ?"
		sql = "Select molecule_id, atom_number, atom.z atomic_number, symbol, name, a, spin, charge, coord.x, coord.y, coord.z From atom Left Join coord Using (molecule_id,atom_number) Where molecule_id = ?"
		sqlargs = [imol]
		self.cursor.execute(sql, sqlargs)
		for row in self.cursor:
			if row['atom_number']:
				atomid = int(row['atom_number'])
				atom = OBAtom()
				atom.SetId(atomid)
				if row['atomic_number']:
					atom.SetAtomicNum(int(row['atomic_number']))
				if row['a']:
					atom.SetIsotope(int(row['a']))
				if row['charge']:
					atom.SetFormalCharge(int(row['charge']))
				if row['spin']:
					atom.SetSpinMultiplicity(int(row['spin']))
				if row['x'] and row['y'] and row['z']:
					atom.SetVector(float(row['x']), float(row['y']), float(row['z']))
				mol.AddAtom(atom)

	def set_stereo(self, imol, mol):
		# deal with stereo atoms in mol
		mol.DeleteData(StereoData)
		self.set_tetrahedral_stereo(imol, mol)
		self.set_cistrans_stereo(imol, mol)

	def set_tetrahedral_stereo(self, imol, mol):
		sql = "Select molecule_id, value From property Where molecule_id = ? And name = 'OBTetrahedralStereo'"
		sqlargs = [imol]
		self.cursor.execute(sql, sqlargs)
		for row in self.cursor:
			stereo = json.loads(row['value'])
			cfg = OBTetrahedralConfig()
			cfg.center = stereo['center']
			cfg.from_or_towards = OBStereo.NoRef if stereo['look'] == 'None' \
					else OBStereo.ImplicitRef if stereo['look'] == 'Implicit' \
					else stereo['look']
			cfg.view = OBStereo.ViewFrom if stereo['view'] == 'From' \
					else OBStereo.ViewTowards
			cfg.winding = OBStereo.Clockwise if stereo['winding'] == 'Clockwise' \
					else OBStereo.AntiClockwise
			cfg.refs = [OBStereo.NoRef if r == 'None' \
					else OBStereo.ImplicitRef if r == 'Implicit' \
					else r for r in stereo['refs']]
			cfg.specified = True
			#print cfg.center, cfg.winding, cfg.refs, cfg.from_or_towards, cfg.view, cfg.specified
			ts = OBTetrahedralStereo(mol)
			ts.SetConfig(cfg)
			mol.CloneData(ts)

	def set_cistrans_stereo(self, imol, mol):
		sql = "Select molecule_id, value From property Where molecule_id = ? And name = 'OBCisTransStereo'"
		sqlargs = [imol]
		self.cursor.execute(sql, sqlargs)
		for row in self.cursor:
			cistrans = json.loads(row['value'])
			cfg = OBCisTransConfig()
			cfg.begin = cistrans['begin']
			cfg.end   = cistrans['end']
			cfg.shape = OBStereo.ShapeU if cistrans['shape'] == 'U' \
					else OBStereo.ShapeZ if cistrans['shape'] == 'Z' \
					else OBStereo.Shape4
			cfg.refs = [OBStereo.NoRef if r == 'None' \
					else OBStereo.ImplicitRef if r == 'Implicit' \
					else r for r in cistrans['refs']]
			cfg.specified = True
			cs = OBCisTransStereo(mol)
			cs.SetConfig(cfg)
			mol.CloneData(cs)

	def make_bonds(self, imol, mol):
		sql = "Select molecule_id, from_atom, to_atom, bond_order From bond Where molecule_id = ?"
		sqlargs = [imol]
		self.cursor.execute(sql, sqlargs)
		for row in self.cursor:
			bond = OBBond()
			if row['from_atom']:
				from_atom = mol.GetAtomById(int(row['from_atom']))
			if row['to_atom']:
				to_atom	= mol.GetAtomById(int(row['to_atom']))
			if row['bond_order']:
				bond_order = int(row['bond_order'])
			bond.SetBegin(from_atom)
			bond.SetEnd(to_atom)
			bond.SetBondOrder(bond_order)
			mol.AddBond(bond)

	def test_stereo(self, mol):
		print 'test stereo',mol.HasChiralityPerceived()
		#facade = OBStereoFacade(mol);
		#for atom in OBMolAtomIter(mol):
		#	if facade.HasTetrahedralStereo(atom.GetId()):
		#		stereo = self.get_atom_stereo(facade,mol,atom)
		#		print atom.GetId(), atom.GetIdx(), stereo
		for p in mol.GetData():
			if p.GetDataType() == StereoData:
				ts = toTetrahedralStereo(p)
				if ts.IsValid():
					cfg = ts.GetConfig()
					stereo = self.stereoCfgToDict(cfg, mol)
					print stereo
				else:
					ct = toCisTransStereo(p)
					cfg = ct.GetConfig()
					cistrans = self.cistransCfgToDict(cfg, mol)
					print cistrans

	def mol_compare(self, imol, mol):
		# is the constructed molecule the same as input?  need valid smiles property
		# compare cansmiles for each
		#self.cursor.execute("Select name,value From property Where molecule_id=? And name like '%smiles%'", [imol])
		self.cursor.execute("Select name,value From property Where molecule_id=? And name = 'OpenBabel cansmiles'", [imol])
		for row in self.cursor:
			name =  str(row['name'])
			insmi =  str(row['value'])
			obc = OBConversion()
			obc.SetInFormat('smi')
			obc.SetOutFormat('can')
			obc.SetOptions("-n", obc.OUTOPTIONS) # no name
			tmpmol = OBMol()
			obc.ReadString(tmpmol, insmi)
			incan = obc.WriteString(tmpmol,1)
			mycan = obc.WriteString(mol,1)
			if mycan != incan:
				# one last try for dot-separated smiles that may have re-ordered fragments
				myfrags = mycan.split('.')
				infrags = incan.split('.')
				myfrags.sort()
				infrags.sort()
				if myfrags != infrags:
					print 'Mismatch:', name, mol.GetTitle(), insmi, incan, mycan
			else:
				pass
				#print 'Match:', name, mol.GetTitle(), insmi, incan, mycan

	def make_mol(self):
		sql = "Select molecule_id,created,charge,name From molecule"
		molcursor = self.connection.cursor()
		molcursor.execute(sql)
		mol = OBMol()
		for row in molcursor:
			if row['molecule_id']:
				imol = int(row['molecule_id'])
				sys.stderr.write(str(imol)+'\r')
			else:
				print 'molecule id error'
				exit(0)
			mol.Clear()
			mol.BeginModify()
			if row['name']:
				title = str(row['name'])
				mol.SetTitle(title)
			if row['charge']:
				charge = int(row['charge'])
				mol.SetTotalCharge(charge)
			self.make_atoms(imol, mol)
			self.make_bonds(imol, mol)
			mol.EndModify()
			if mol.Has3D():
				mol.SetDimension(3)
			elif mol.Has2D():
				mol.SetDimension(2)
			else:
				mol.SetDimension(0)
			self.set_stereo(imol, mol)
			#self.test_stereo(mol)
			self.mol_compare(imol, mol)
		self.close()

import sys
if __name__ == '__main__':

	if len(sys.argv) == 1:
		exit(0)
	db = sys.argv[1]
	u = umdb(db)
