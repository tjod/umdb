CREATE TABLE molecule
(
molecule_id INTEGER PRIMARY KEY,
created TIMESTAMP,
title TEXT
);

CREATE TABLE atom
(
atom_id INTEGER PRIMARY KEY,
molecule_id INTEGER NOT NULL REFERENCES molecule (molecule_id)  ON DELETE CASCADE ON UPDATE RESTRICT,
type TEXT,
number INTEGER,
symbol TEXT,
isotope INTEGER,
atomic_number INTEGER,
spin INTEGER,
formal_charge FLOAT,
partial_charge FLOAT
);

CREATE TABLE atom_property
(
atom_prop_id INTEGER PRIMARY KEY,
atom_id INTEGER NOT NULL REFERENCES atom (atom_id)  ON DELETE CASCADE ON UPDATE RESTRICT,
name TEXT,
value TEXT
);

CREATE TABLE bond
(
bond_id INTEGER PRIMARY KEY,
a_id INTEGER NOT NULL REFERENCES atom (atom_id)  ON DELETE CASCADE ON UPDATE RESTRICT,
b_id INTEGER NOT NULL REFERENCES atom (atom_id)  ON DELETE CASCADE ON UPDATE RESTRICT,
bond_order FLOAT,
bond_type TEXT
);

CREATE TABLE bond_property
(
bond_prop_id INTEGER PRIMARY KEY,
bond_id INTEGER NOT NULL REFERENCES bond (bond_id)  ON DELETE CASCADE ON UPDATE RESTRICT,
name TEXT,
value TEXT
);

CREATE TABLE coord
(
coord_id INTEGER PRIMARY KEY,
atom_id INTEGER NOT NULL REFERENCES atom (atom_id)  ON DELETE CASCADE ON UPDATE RESTRICT,
set_number INTEGER,
x FLOAT,
y FLOAT,
z FLOAT
);

CREATE TABLE internal_coord
(
int_coord_id INTEGER PRIMARY KEY,
a_id INTEGER NOT NULL REFERENCES atom (atom_id)  ON DELETE CASCADE ON UPDATE RESTRICT,
b_id INTEGER NOT NULL REFERENCES atom (atom_id)  ON DELETE CASCADE ON UPDATE RESTRICT,
c_id INTEGER NOT NULL REFERENCES atom (atom_id)  ON DELETE CASCADE ON UPDATE RESTRICT,
distance FLOAT,
angle FLOAT,
torsion FLOAT
);

CREATE TABLE molecule_property
(
mol_prop_id INTEGER PRIMARY KEY,
name TEXT,
value TEXT,
molecule_id INTEGER NOT NULL REFERENCES molecule (molecule_id)  ON DELETE CASCADE ON UPDATE RESTRICT
);

CREATE TABLE residue
(
res_id INTEGER PRIMARY KEY,
molecule_id INTEGER NOT NULL REFERENCES molecule  (molecule_id)  ON DELETE CASCADE ON UPDATE RESTRICT,
number INTEGER NOT NULL,
name TEXT, 
chain TEXT
);

CREATE TABLE residue_atom
(
res_atom_id INTEGER PRIMARY KEY,
atom_id INTEGER NOT NULL REFERENCES atom (atom_id)  ON DELETE CASCADE ON UPDATE RESTRICT,
res_id  INTEGER NOT NULL REFERENCES residue (res_id)  ON DELETE CASCADE ON UPDATE RESTRICT,
name TEXT
);

-- View into bond table using molecule id and atom numbers in place of atom id's
-- Select * From bonds;
-- Select title,natoms,nbonds from bonds Join molecule Using (molecule_id);
-- Select * From bonds Where moleclue_id In (Select moleclule_id From molecule where title = 'celecoxib');
Create View bonds As Select molecule_id, a.number From_atom, b.number to_atom From Atom a Join atom b Using (molecule_id) Join bond On (a_id = a.atom_id And b_id = b.atom_id);

-- Count of atoms and bonds in each moleclue.
-- Select * From atom_bond_count;
-- Select * From atom_bond_count Where molecule_id Between 2 And 6;;
Create View atom_bond_count As Select molecule_id, Count(Distinct atom_id) natoms, Count(Distinct bond_id) nbonds From atom Left Join bond On (atom_id=a_id Or atom_id=b_id) Group By molecule_id;;
