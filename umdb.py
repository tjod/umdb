import sqlite3
from openbabel import *

class umdb:
    def __init__(self, out):
        self.connection = sqlite3.connect(out)
        self.cursor = self.connection.cursor()
        self.molid = 0
	self.cursor.execute("Pragma foreign_keys=1")
	#self.cursor.execute("Pragma synchronous=OFF")
	self.cursor.execute("Begin")
        print "Begin"

    def insert_mol(self, obmol, bonds=True):
        sqlargs = [obmol.GetTitle()]
        sql = "Insert into molecule (created, title) Values (datetime('now'), ?)"
        self.cursor.execute(sql, sqlargs)
        self.molid = self.cursor.lastrowid
        self.insert_molproperties(obmol)
        self.insert_residues(obmol)
        self.insert_atoms(obmol)
        self.insert_atomproperties(obmol)
        self.connection.commit()
        if bonds:
            self.insert_bonds(obmol)
            self.insert_bondproperties(obmol)

    def insert_molproperty(self, name, value):
        sql = "Insert Into molecule_property (molecule_id, name, value) Values (?,?,?)"
        sqlargs = [self.molid, name, value]
        self.cursor.execute(sql, sqlargs)

    def close(self):
        self.connection.commit()
        self.connection.close()
        print "End"

    def insert_atomproperties(self, obmol):
        sql = "Insert into atom_property (molecule_id, atom_number, name, value) Values (?,?,?,?)"
        for atom in OBMolAtomIter(obmol):
          for p in atom.GetData():
            if toPairData(p).GetDataType() == PairData:
                if p.GetAttribute() == 'OpenBabel Symmetry Classes':
                    pass
                else:
                    sqlargs = [self.molid, atom.GetIdx(), p.GetAttribute(), p.GetValue()]
                    self.cursor.execute(sql, sqlargs)

    def insert_molproperties(self, obmol):
        sql = "Insert into molecule_property (molecule_id, name, value) Values (?,?,?)"
        for p in obmol.GetData():
            if toPairData(p).GetDataType() == PairData:
                if p.GetAttribute() == 'OpenBabel Symmetry Classes':
                    pass
                else:
                    sqlargs = [self.molid, p.GetAttribute(), p.GetValue()]
                    self.cursor.execute(sql, sqlargs)

    def insert_residues(self, obmol):
        ressql = "Insert into residue (molecule_id, name, number, chain) Values (?,?,?,?)"
        for res in OBResidueIter(obmol):
            sqlargs = [self.molid, res.GetName(), res.GetNum(), res.GetChain()]
            self.cursor.execute(ressql, sqlargs)

    def insert_atoms(self, obmol):
        atomsql = "Insert into atom (molecule_id, number, atomic_number, symbol, type, isotope, spin, formal_charge, partial_charge) Values (?,?,?,?,?,?,?,?,?)"
        coordsql = "Insert into coord (molecule_id, atom_number, x, y, z) Values (?,?,?,?,?)";
        ressql = "Insert into residue_atom (molecule_id, res_number, chain, atom_number, name) Values (?,?,?,?,?)"
        for atom in OBMolAtomIter(obmol):
            sqlargs = [self.molid, atom.GetIdx(), atom.GetAtomicNum(), OBElementTable().GetSymbol(atom.GetAtomicNum()), atom.GetType(), atom.GetIsotope(), atom.GetSpinMultiplicity(), atom.GetFormalCharge(), atom.GetPartialCharge()]
            self.cursor.execute(atomsql, sqlargs)
            # store atom coords
            sqlargs = [self.molid, atom.GetIdx(), atom.x(), atom.y(), atom.z()]
            self.cursor.execute(coordsql, sqlargs)
            # store atom name in residue (pdb)
            if atom.HasResidue():
                res = atom.GetResidue()
                atom_name = res.GetAtomID(atom)
                sqlargs = [self.molid,  res.GetNum(), res.GetChain(), atom.GetIdx(), atom_name]
                self.cursor.execute(ressql, sqlargs)

    def insert_bonds(self, obmol):
        sql = "Insert into bond (molecule_id, from_atom, to_atom, bond_order) Values (?,?,?,?)"
        for bond in OBMolBondIter(obmol):
            sqlargs = [self.molid, bond.GetBeginAtomIdx(), bond.GetEndAtomIdx(), bond.GetBondOrder()]
            self.cursor.execute(sql, sqlargs)

    def insert_bondproperties(self, obmol):
        sql = "Insert into bond_property (molecule_id, from_atom, to_atom, name, value) Values (?,?,?,?,?)"
        for bond in OBMolBondIter(obmol):
          for p in bond.GetData():
            if toPairData(p).GetDataType() == PairData:
                if p.GetAttribute() == 'OpenBabel Symmetry Classes':
                    pass
                else:
                    sqlargs = [self.molid, bond.GetBeginAtomIdx(), bond.GetEndAtomIdx(), p.GetAttribute(), p.GetValue()]
                    self.cursor.execute(sql, sqlargs)
