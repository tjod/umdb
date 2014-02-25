CREATE TABLE molecule
(
molecule_id INTEGER PRIMARY KEY,
created TIMESTAMP,
title TEXT
);

CREATE TABLE atom
(
molecule_id INTEGER NOT NULL REFERENCES molecule (molecule_id) ON DELETE CASCADE ON UPDATE RESTRICT,
type TEXT,
number INTEGER,
symbol TEXT,
isotope INTEGER,
atomic_number INTEGER,
spin INTEGER,
formal_charge FLOAT,
partial_charge FLOAT,
PRIMARY KEY (molecule_id, number)
);

CREATE TABLE atom_property
(
molecule_id INTEGER NOT NULL,
atom_number INTEGER NOT NULL,
name TEXT,
value TEXT,
PRIMARY KEY (molecule_id, atom_number)
FOREIGN KEY (molecule_id, atom_number) REFERENCES atom (molecule_id, number) ON DELETE CASCADE ON UPDATE RESTRICT
);

CREATE TABLE bond
(
molecule_id INTEGER NOT NULL,
from_atom INTEGER NOT NULL,
to_atom INTEGER NOT NULL,
bond_order FLOAT,
bond_type TEXT,
PRIMARY KEY (molecule_id, from_atom, to_atom),
FOREIGN KEY (molecule_id, from_atom) REFERENCES atom (molecule_id, number) ON DELETE CASCADE ON UPDATE RESTRICT,
FOREIGN KEY (molecule_id, to_atom)  REFERENCES atom (molecule_id, number) ON DELETE CASCADE ON UPDATE RESTRICT
);

CREATE TABLE bond_property
(
molecule_id INTEGER NOT NULL,
from_atom INTEGER NOT NULL,
to_atom INTEGER NOT NULL,
name TEXT,
value TEXT,
PRIMARY KEY (molecule_id, from_atom, to_atom),
FOREIGN KEY (molecule_id, from_atom, to_atom) REFERENCES bond (molecule_id, from_atom, to_atom) ON DELETE CASCADE ON UPDATE RESTRICT
);

CREATE TABLE coord
(
molecule_id INTEGER NOT NULL,
atom_number INTEGER NOT NULL,
set_number INTEGER,
x FLOAT,
y FLOAT,
z FLOAT,
PRIMARY KEY (molecule_id, atom_number),
FOREIGN KEY (molecule_id, atom_number) REFERENCES atom (molecule_id, number) ON DELETE CASCADE ON UPDATE RESTRICT
);

CREATE TABLE internal_coord
(
molecule_id INTEGER NOT NULL,
atom_number INTEGER NOT NULL,
a_number INTEGER,
distance FLOAT,
b_number INTEGER,
angle FLOAT,
c_number INTEGER,
torsion FLOAT,
PRIMARY KEY (molecule_id, atom_number),
FOREIGN KEY (molecule_id, atom_number) REFERENCES atom (molecule_id, number) ON DELETE CASCADE ON UPDATE RESTRICT,
FOREIGN KEY (molecule_id, a_number) REFERENCES atom (molecule_id, number) ON DELETE CASCADE ON UPDATE RESTRICT,
FOREIGN KEY (molecule_id, b_number) REFERENCES atom (molecule_id, number) ON DELETE CASCADE ON UPDATE RESTRICT,
FOREIGN KEY (molecule_id, c_number) REFERENCES atom (molecule_id, number) ON DELETE CASCADE ON UPDATE RESTRICT
);

CREATE TABLE molecule_property
(
name TEXT,
value TEXT,
molecule_id INTEGER NOT NULL REFERENCES molecule (molecule_id) ON DELETE CASCADE ON UPDATE RESTRICT
);

CREATE TABLE residue
(
molecule_id INTEGER NOT NULL REFERENCES molecule (molecule_id) ON DELETE CASCADE ON UPDATE RESTRICT,
number INTEGER NOT NULL,
name TEXT, 
chain TEXT,
PRIMARY KEY (molecule_id, chain, number)
);

CREATE TABLE residue_atom
(
molecule_id INTEGER NOT NULL,
res_number INTEGER NOT NULL,
chain TEXT NOT NULL,
atom_number INTEGER NOT NULL,
name TEXT,
PRIMARY KEY (molecule_id, chain, res_number, atom_number),
FOREIGN KEY (molecule_id, chain, res_number) REFERENCES residue (molecule_id, chain, number) ON DELETE CASCADE ON UPDATE RESTRICT,
FOREIGN KEY (molecule_id, atom_number) REFERENCES atom (molecule_id, number) ON DELETE CASCADE ON UPDATE RESTRICT
);

-- Count of atoms and bonds in each molecule.
--Create View atom_bond_count As
-- With atom_count As (Select molecule_id,count(*) From atom Group By molecule_id),
--      bond_count As (Select molecule_id,count(*) From bond Group By molecule_id)
--Select * From atom_count Join bond_count Using (molecule_id);
Create View mol_atom_bond_count As Select molecule_id, natoms, nbonds
 From (Select molecule_id, Count(*) As natoms From atom Group By molecule_id) atom_count
 Join (Select molecule_id, Count(*) As nbonds From bond Group By molecule_id) bond_count Using (molecule_id);
-- Possible uses:
-- Select * From atom_bond_count;
-- Select * From atom_bond_count Where molecule_id Between 2 And 6;;
-- Select * From atom_bond_count Join molecule Using (molecule_id) Where title="some title";

-- Summary of atoms in each residue
Create View mol_res_atoms As Select res.molecule_id, res.chain, name, res_number, atom_list, natoms
 From (Select molecule_id, chain, res_number, group_concat(atom_number) atom_list, Count(*) As natoms From residue_atom Group By molecule_id,chain,res_number) atoms
 Join residue As res On (res.molecule_id=atoms.molecule_id And res.number=atoms.res_number And res.chain=atoms.chain);

-- Protein sequence
Create View sequence As Select chain, Group_concat(name||number,' ') sequence From residue Where name != 'HOH' Group By chain;
-- Possible uses:
-- Select * From sequence;
-- Select * From sequence Where chain='A';
