#import sqlite3
import openbabel as ob
import json
from umdb import umdb as umdbCore

class umdb:
	"""create umdb file to read files in openbabel supported formats; relies on umdb.py"""
	def __init__(self, out):
		"""out is output database name"""
		#self.molid = 0
		# workaround
		ob.OBStereo.NoRef = 4294967295
		ob.OBStereo.ImplicitRef = 4294967294
		self.ElementTable = ob.OBElementTable()
		if out:
			self.db = umdbCore(out)

	def create(self):
		"""create the umdb file"""
		self.db.create()

	def close(self):
		"""commit and close umdb file"""
		self.db.commit()
		self.db.close()

#	def get_atom_stereo(self, facade, obmol, atom):
#		f = facade.GetTetrahedralStereo(atom.GetId())
#		cfg = f.GetConfig()
#		assert cfg.center == atom.GetId()
#		return self.stereoCfgToDict(cfg, obmol)

	def stereoCfgToDict(self, cfg, obmol):
		"""internal use: parse openbabel atom stereo configuration object into python dictionary"""
		stereo = dict()
		stereo['specified'] = cfg.specified
		stereo['center'] = obmol.GetAtomById(cfg.center).GetIdx()
		stereo['winding'] = 'Clockwise' if cfg.winding == ob.OBStereo.Clockwise \
				else 'AntiClockwise'
		stereo['view'] = 'From' if cfg.view == ob.OBStereo.ViewFrom \
				else 'Towards'
		stereo['look'] = 'None' if cfg.from_or_towards == ob.OBStereo.NoRef \
				else 'Implicit' if cfg.from_or_towards == ob.OBStereo.ImplicitRef \
				else obmol.GetAtomById(cfg.from_or_towards).GetIdx()
		stereo['refs'] = ['None' if r == ob.OBStereo.NoRef \
				else 'Implicit' if r == ob.OBStereo.ImplicitRef \
				else obmol.GetAtomById(r).GetIdx() for r in cfg.refs]
		return stereo

	def cistransCfgToDict(self, cfg, obmol):
		"""internal use: parse openbabel bond stereo configuration object into python dictionary"""
		cistrans = dict()
		cistrans['specified'] = cfg.specified
		cistrans['begin'] = obmol.GetAtomById(cfg.begin).GetIdx()
		cistrans['end']   = obmol.GetAtomById(cfg.end).GetIdx()
		cistrans['shape'] = 'U' if cfg.shape == ob.OBStereo.ShapeU \
				else 'Z' if cfg.shape == ob.OBStereo.ShapeZ \
				else '4'
		cistrans['refs'] = ['None' if r == ob.OBStereo.NoRef \
				else 'Implicit' if r == ob.OBStereo.ImplicitRef \
				else obmol.GetAtomById(r).GetIdx() for r in cfg.refs]
		return cistrans

	def insert_mol(self, obmol, bonds=True):
		"""insert new molecule into umdb"""
		name = obmol.GetTitle()
		self.db.insert_molecule(name)
		# option in main now
		#self.insert_molproperties(obmol)
		self.insert_residues(obmol)
		self.insert_atoms(obmol)
		self.insert_atomproperties(obmol)
		if bonds:
			self.insert_bonds(obmol)
			self.insert_bondproperties(obmol)
		self.db.commit()
		
	def insert_context(self, prefix, suffix):
		"""insert a bond property for current molecule"""
		self.db.insert_context(prefix, suffix)

	def insert_molproperty(self, name, value, ns=None):
		"""insert a molecule property for current molecule"""
		self.db.insert_molproperty(name, value, ns=ns)

	def insert_atomproperty(self, atom_number, name, value, ns=None):
		"""insert an atom property for current molecule"""
		self.db.insert_atomproperty(atom_number, name, value, ns=ns)

	def insert_bondproperty(self, atoma, atomb, name, value, ns=None):
		"""insert a bond property for current molecule"""
		self.db.insert_bondproperty(atoma, atomb, name, value, ns=ns)

	def insert_atomproperties(self, obmol):
		"""loop over openbabel atoms' properties and insert each"""
		for atom in ob.OBMolAtomIter(obmol):
			for p in atom.GetAllData(0):
				self.db.insert_atomproperty(atom.GetIdx(), p.GetAttribute(), p.GetValue())

	def insert_atomtypes(self, obmol):
		"""loop over openbabel atoms' types and insert each"""
		for atom in ob.OBMolAtomIter(obmol):
			atype = atom.GetType()
			if atype:
				self.db.insert_atomproperty(atom.GetIdx(), 'OBType', atype)

	def insert_atomcharges(self, obmol):
		"""loop over openbabel atoms' Partial Charge and insert each"""
		for atom in ob.OBMolAtomIter(obmol):
			partial = atom.GetPartialCharge()
			if partial:
				self.db.insert_atomproperty(atom.GetIdx(), 'GasteigerPartialCharge', partial)

	def cansmiles_atom_order(self, obmol):
		"""insert openbabel canonical(smiles) atom order"""
		for p in obmol.GetData():
			if p.GetDataType() == ob.PairData:
				if p.GetAttribute() == 'SMILES Atom Order':
					return map(int, p.GetValue().split())

	def insert_molproperties(self, obmol):
		"""loop over openbabel mols' Properties and insert each"""
		for p in obmol.GetData():
			if p.GetDataType() == ob.PairData:
				if p.GetAttribute() == 'OpenBabel Symmetry Classes': continue
				self.db.insert_molproperty(p.GetAttribute(), p.GetValue())
			elif p.GetDataType() == ob.StereoData:
				ts = ob.toTetrahedralStereo(p)
				if ts.IsValid():
					cfg = ts.GetConfig()
					#print 'stereo',self.stereoCfgToDict(cfg, obmol)
					if cfg.specified:
						self.db.insert_molproperty('OBTetrahedralStereo', json.dumps(self.stereoCfgToDict(cfg, obmol)))
				else:
					ct = ob.toCisTransStereo(p)
					cfg = ct.GetConfig()
					#print 'cistrans',self.cistransCfgToDict(cfg, obmol)
					if cfg.specified:
						self.db.insert_molproperty('OBCisTransStereo', json.dumps(self.cistransCfgToDict(cfg, obmol)))

	def insert_residues(self, obmol):
		"""insert residues of a (pdb)molecule"""
		for res in ob.OBResidueIter(obmol):
			self.db.insert_residue(res.GetName(), res.GetNum(), res.GetChain())

	def insert_atoms(self, obmol):
		"""loop over all atoms in molecule and insert them"""
		for atom in ob.OBMolAtomIter(obmol):
			isotope = int(atom.GetIsotope())
			charge = int(atom.GetFormalCharge())
			spin = int(atom.GetSpinMultiplicity())
			name = atom.GetTitle()
			z=atom.GetAtomicNum()
			symbol=self.ElementTable.GetSymbol(z)
			if isotope == 0:
				isotope = None #isotope = int(ob.OBIsotopeTable().GetExactMass (atom.GetAtomicNum()))
			if spin == 0:
				spin = None
			self.db.insert_atom(atom.GetIdx(), z=z, symbol=symbol, name=name, isotope=isotope, spin=spin, charge=charge)
			# store atom coords
			if obmol.GetDimension() > 0:
				self.db.insert_atom_coord(atom.GetIdx(), atom.x(), atom.y(), atom.z())
			# store atom name in residue (pdb)
			if atom.HasResidue():
				res = atom.GetResidue()
				atom_name = res.GetAtomID(atom)
				self.db.insert_residue_atom(res.GetNum(), res.GetChain(), atom.GetIdx(), atom_name)

			# goes into molecule property now
			#if facade.HasTetrahedralStereo(atom.GetId()):
			#	stereo = self.get_atom_stereo(facade, obmol, atom)
			#	self.insert_property(atom.GetIdx(), 'OBStereo', json.dumps(stereo))

	def insert_bonds(self, obmol):
		"""loop over bonds in molecule and insert them"""
		for bond in ob.OBMolBondIter(obmol):
			self.db.insert_bond(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx(), bond.GetBondOrder())

	def insert_bondproperties(self, obmol):
		"""loop over bonds' properties and insert them"""
		for bond in ob.OBMolBondIter(obmol):
			for p in bond.GetData():
				if ob.toPairData(p).GetDataType() == ob.PairData:
					self.db.insert_bondproperty(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx(), p.GetAttribute(), p.GetValue())

# the following read db and create OBMol and other OB* objects

	def make_atoms(self, imol, mol):
		"""add OBAtom() to mol for all atoms in database molecule_id==imol"""
		sql = "Select molecule_id, atom_number, atom.z atomic_number, symbol, name, a, spin, charge, coord.x, coord.y, coord.z From atom Left Join coord Using (molecule_id,atom_number) Where molecule_id = ?"
		sqlargs = [imol]
		self.db.cursor.execute(sql, sqlargs)
		for row in self.db.cursor:
			if row['atom_number']:
				atomid = int(row['atom_number'])
				atom = ob.OBAtom()
				atom.SetId(atomid)
				if row['atomic_number'] is not None:
					atom.SetAtomicNum(int(row['atomic_number']))
				if row['a'] is not None:
					atom.SetIsotope(int(row['a']))
				if row['charge'] is not None:
					atom.SetFormalCharge(int(row['charge']))
				if row['spin'] is not None:
					atom.SetSpinMultiplicity(int(row['spin']))
				if row['x']  is not None and row['y'] is not None and row['z'] is not None:
					atom.SetVector(float(row['x']), float(row['y']), float(row['z']))
				mol.AddAtom(atom)

	def set_stereo(self, imol, mol):
		"""deal with stereo atoms in mol"""
		mol.DeleteData(ob.StereoData)
		self.set_tetrahedral_stereo(imol, mol)
		self.set_cistrans_stereo(imol, mol)

	def set_tetrahedral_stereo(self, imol, mol):
		"""internal use: called by set_stereo to set openbabel atom stereo configuration"""
		sql = "Select molecule_id, value From property Where molecule_id = ? And name = 'OBTetrahedralStereo'"
		sqlargs = [imol]
		self.db.cursor.execute(sql, sqlargs)
		for row in self.db.cursor:
			stereo = json.loads(row['value'])
			cfg = ob.OBTetrahedralConfig()
			cfg.center = stereo['center']
			cfg.from_or_towards = ob.OBStereo.NoRef if stereo['look'] == 'None' \
					else ob.OBStereo.ImplicitRef if stereo['look'] == 'Implicit' \
					else stereo['look']
			cfg.view = ob.OBStereo.ViewFrom if stereo['view'] == 'From' \
					else ob.OBStereo.ViewTowards
			cfg.winding = ob.OBStereo.Clockwise if stereo['winding'] == 'Clockwise' \
					else ob.OBStereo.AntiClockwise
			cfg.refs = [ob.OBStereo.NoRef if r == 'None' \
					else ob.OBStereo.ImplicitRef if r == 'Implicit' \
					else r for r in stereo['refs']]
			cfg.specified = True
			#print cfg.center, cfg.winding, cfg.refs, cfg.from_or_towards, cfg.view, cfg.specified
			ts = ob.OBTetrahedralStereo(mol)
			ts.SetConfig(cfg)
			mol.CloneData(ts)

	def set_cistrans_stereo(self, imol, mol):
		"""internal use: called by set_stereo to set openbabel bond stereo configuration"""
		sql = "Select molecule_id, value From property Where molecule_id = ? And name = 'OBCisTransStereo'"
		sqlargs = [imol]
		self.db.cursor.execute(sql, sqlargs)
		for row in self.db.cursor:
			cistrans = json.loads(row['value'])
			cfg = ob.OBCisTransConfig()
			cfg.begin = cistrans['begin']
			cfg.end   = cistrans['end']
			cfg.shape = ob.OBStereo.ShapeU if cistrans['shape'] == 'U' \
					else ob.OBStereo.ShapeZ if cistrans['shape'] == 'Z' \
					else ob.OBStereo.Shape4
			cfg.refs = [ob.OBStereo.NoRef if r == 'None' \
					else ob.OBStereo.ImplicitRef if r == 'Implicit' \
					else r for r in cistrans['refs']]
			cfg.specified = True
			cs = ob.OBCisTransStereo(mol)
			cs.SetConfig(cfg)
			mol.CloneData(cs)

	def make_bonds(self, imol, mol):
		"""add OBBond() to mol for all bonds in database molecule_id==imol"""
		sql = "Select molecule_id, from_atom, to_atom, bond_order From bond Where molecule_id = ?"
		sqlargs = [imol]
		self.db.cursor.execute(sql, sqlargs)
		for row in self.db.cursor:
			bond = ob.OBBond()
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
		"""test of successful use of atom and bond stereo configurations"""
		print 'test stereo',mol.HasChiralityPerceived()
		#facade = ob.OBStereoFacade(mol);
		#for atom in ob.OBMolAtomIter(mol):
		#	if facade.HasTetrahedralStereo(atom.GetId()):
		#		stereo = self.get_atom_stereo(facade,mol,atom)
		#		print atom.GetId(), atom.GetIdx(), stereo
		for p in mol.GetData():
			if p.GetDataType() == ob.StereoData:
				ts = ob.toTetrahedralStereo(p)
				if ts.IsValid():
					cfg = ts.GetConfig()
					stereo = self.stereoCfgToDict(cfg, mol)
					print stereo
				else:
					ct = ob.toCisTransStereo(p)
					cfg = ct.GetConfig()
					cistrans = self.cistransCfgToDict(cfg, mol)
					print cistrans

	def mol_compare(self, imol, mol):
		"""compare openbabel cansmiles stored in db where molecule_id=imol with OBConversion() producting cansmiles for OBMol() mol"""
		# is the constructed molecule the same as input?  need valid smiles property
		#self.cursor.execute("Select name,value From property Where molecule_id=? And name like '%smiles%'", [imol])
		self.db.cursor.execute("Select name,value From property Where molecule_id=? And name = 'OpenBabel cansmiles'", [imol])
		for row in self.db.cursor:
			#name =  str(row['name'])
			insmi =  str(row['value'])
			obc = ob.OBConversion()
			obc.SetInFormat('smi')
			obc.SetOutFormat('can')
			obc.SetOptions("-n", obc.OUTOPTIONS) # no name
			tmpmol = ob.OBMol()
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
					print 'Mismatch:', mol.GetTitle(), insmi
					print incan
					print mycan
			else:
				pass
				#print 'Match:', name, mol.GetTitle(), insmi, incan, mycan

	def make_mol(self, imol, row=None):
		"""make an OBMol from database where molecule_id=imol); for imol or optionally row of already selected db mol"""
		if imol == None: return None
		mol = ob.OBMol()
		mol.Clear()
		mol.BeginModify()
		if row == None:
			sql = "Select molecule_id,created,charge,name From molecule Where molecule_id=?"
			molcursor = self.db.connection.cursor()
			molcursor.execute(sql, [imol])
			row = molcursor.fetchone()
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
		return mol

	def compare_mols(self, compare=False, fmt='can', line_numbers=True, molnames=True):
		"""compare cansmiles of OBMol() constructed from database mols with openbabel cansmiles stored as property.
		   This only makes sense when there is a name='OpenBabel cansmiles' in the property table.
		"""
		obc = ob.OBConversion()
		obc.SetOutFormat(fmt)
		obc.SetOptions("-n", obc.OUTOPTIONS) # no name
		sql = "Select molecule_id,created,charge,name From molecule"
		molcursor = self.db.connection.cursor()
		molcursor.execute(sql)
		for row in molcursor:
			if row['molecule_id']:
				imol = int(row['molecule_id'])
			else:
				print 'molecule id error'
				exit(0)
			mol = self.make_mol(imol, row=row)
			#self.test_stereo(mol)
			if (compare):
				sys.stderr.write(str(imol)+'\r')
				self.mol_compare(imol, mol)
			else:
				out = obc.WriteString(mol,1)
				if line_numbers: print imol,":",
				print out,
				if molnames: print mol.GetTitle(),
				print

import sys
if __name__ == '__main__':

	if len(sys.argv) == 1:
		exit(0)
	db = sys.argv[1]
	u = umdbCore(db)
