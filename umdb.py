import sqlite3
from openbabel import *

class umdb:
    def __init__(self, out):
        self.connection = sqlite3.connect(out)
        self.cursor = self.connection.cursor()
        self.molid = 0
	self.cursor.execute("Pragma foreign_keys=1")

    def insert_mol(self, obmol, bonds=True):
        sqlargs = [obmol.GetTitle()]
        sql = "Insert into molecule (created, title) Values (datetime('now'), ?)"
        self.cursor.execute(sql, sqlargs)
        self.molid = self.cursor.lastrowid
        self.insert_molproperties(obmol)
        self.insert_residues(obmol)
        self.insert_atoms(obmol)
        if bonds: self.insert_bonds(obmol)
        self.connection.commit()
        self.connection.close()

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
        coordsql = "Insert into coord (atom_id, x, y, z) Values (?,?,?,?)";
        ressql = "Insert into residue_atom (res_id, atom_id, name) Select res_id,?,? From residue Where molecule_id=? And number=? And chain=?"
        for atom in OBMolAtomIter(obmol):
            sqlargs = [self.molid, atom.GetIdx(), atom.GetAtomicNum(), OBElementTable().GetSymbol(atom.GetAtomicNum()), atom.GetType(), atom.GetIsotope(), atom.GetSpinMultiplicity(), atom.GetFormalCharge(), atom.GetPartialCharge()]
            self.cursor.execute(atomsql, sqlargs)
            atom_id = self.cursor.lastrowid
            # store atom coords
            sqlargs = [atom_id, atom.x(), atom.y(), atom.z()]
            self.cursor.execute(coordsql, sqlargs)
            # store atom name in residue (pdb)
            if atom.HasResidue():
                res = atom.GetResidue()
                atom_name = res.GetAtomID(atom)
                sqlargs = [atom_id, atom_name, self.molid, res.GetNum(), res.GetChain()]
                self.cursor.execute(ressql, sqlargs)

    def insert_bonds(self, obmol):
        #sql = "Insert into bond (molecule_id, a_number, b_number, bond_order) Values (?,?,?,?)"
        sql = "Insert into bond (a_id, b_id, bond_order) Select a.atom_id, b.atom_id, ? from atom a join atom b Using (molecule_id) where molecule_id=? and a.number=? and b.number=? "
        for bond in OBMolBondIter(obmol):
            sqlargs = [bond.GetBondOrder(), self.molid, bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()]
            self.cursor.execute(sql, sqlargs)
