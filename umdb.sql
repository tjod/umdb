CREATE TABLE If Not Exists molecule (
                molecule_id INTEGER PRIMARY KEY,
		charge INTEGER,
		multiplicity INTEGER,
                created TIMESTAMP,
                name TEXT
);


CREATE TABLE If Not Exists property (
                molecule_id INTEGER NOT NULL,
		ns TEXT,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
		FOREIGN KEY (molecule_id) REFERENCES molecule (molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
		FOREIGN KEY (molecule_id, ns) REFERENCES graph_context (molecule_id, prefix)
);
CREATE INDEX If Not Exists property_idx ON property (molecule_id);


CREATE TABLE If Not Exists atom (
                molecule_id INTEGER NOT NULL,
                atom_number INTEGER NOT NULL,
                symbol TEXT,
		name TEXT,
                z INTEGER, -- atomic number
                a INTEGER, -- isostope number
                spin INTEGER,
                charge INTEGER, -- formal charge
                CONSTRAINT atom_pkey PRIMARY KEY (molecule_id, atom_number)
		FOREIGN KEY (molecule_id) REFERENCES molecule (molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE If Not Exists bond (
                molecule_id INTEGER NOT NULL,
                from_atom INTEGER NOT NULL,
                to_atom INTEGER NOT NULL,
		name TEXT,
                bond_order FLOAT,
                --bond_type TEXT,
                CONSTRAINT bond_pkey PRIMARY KEY (molecule_id, from_atom, to_atom)
		FOREIGN KEY (molecule_id, from_atom) REFERENCES atom (molecule_id, atom_number) ON DELETE CASCADE ON UPDATE CASCADE
		FOREIGN KEY (molecule_id, to_atom) REFERENCES atom (molecule_id, atom_number) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE If Not Exists atom_property (
                molecule_id INTEGER NOT NULL,
                atom_number INTEGER NOT NULL,
		ns TEXT,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
		FOREIGN KEY (molecule_id, atom_number) REFERENCES atom (molecule_id, atom_number) ON DELETE CASCADE ON UPDATE CASCADE
		FOREIGN KEY (molecule_id, ns) REFERENCES graph_context (molecule_id, prefix)
);
CREATE INDEX If Not Exists atom_property_idx ON atom_property (molecule_id, atom_number);

CREATE TABLE If Not Exists bond_property (
                molecule_id INTEGER NOT NULL,
                from_atom INTEGER NOT NULL,
                to_atom INTEGER NOT NULL,
		ns TEXT,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
		FOREIGN KEY (molecule_id, from_atom, to_atom) REFERENCES bond (molecule_id, from_atom, to_atom) ON DELETE CASCADE ON UPDATE CASCADE
		FOREIGN KEY (molecule_id, ns) REFERENCES graph_context (molecule_id, prefix)
);
CREATE INDEX If Not Exists bond_property_idx ON bond_property (molecule_id, from_atom, to_atom);


CREATE TABLE If Not Exists coord (
                molecule_id INTEGER NOT NULL,
                atom_number INTEGER NOT NULL,
                set_number INTEGER,
                x DOUBLE,
                y DOUBLE,
                z DOUBLE,
                CONSTRAINT coord_pkey PRIMARY KEY (molecule_id, atom_number)
		FOREIGN KEY (atom_number, molecule_id) REFERENCES atom (atom_number, molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE If Not Exists internal_coord (
                molecule_id INTEGER NOT NULL,
		atom_number INTEGER NOT NULL,
                distance_atom INTEGER,
                distance DOUBLE,
                angle_atom INTEGER,
                angle DOUBLE,
                torsion_atom INTEGER,
                torsion DOUBLE,
                CONSTRAINT internal_coord_pkey PRIMARY KEY (molecule_id, atom_number)
		FOREIGN KEY (atom_number, molecule_id) REFERENCES atom (atom_number, molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
		FOREIGN KEY (distance_atom, molecule_id) REFERENCES atom (atom_number, molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
		FOREIGN KEY (angle_atom, molecule_id) REFERENCES atom (atom_number, molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
		FOREIGN KEY (torsion_atom, molecule_id) REFERENCES atom (atom_number, molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE If Not Exists residue (
                molecule_id INTEGER NOT NULL,
		chain TEXT,
		number INTEGER,
		name TEXT,
                CONSTRAINT residue_pkey PRIMARY KEY (molecule_id, chain, number)
		FOREIGN KEY (molecule_id) REFERENCES molecule (molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE If Not Exists residue_atom (
                molecule_id INTEGER NOT NULL,
		atom_number INTEGER NOT NULL,
		chain TEXT NOT NULL,
		number INTEGER NOT NULL,
		name TEXT,
                CONSTRAINT residue_atom_pkey PRIMARY KEY (molecule_id, atom_number)
		FOREIGN KEY (molecule_id, atom_number) REFERENCES atom (molecule_id, atom_number) ON DELETE CASCADE ON UPDATE CASCADE
		FOREIGN KEY (molecule_id, chain, number) REFERENCES residue (molecule_id, chain, number) ON DELETE CASCADE ON UPDATE CASCADE
);

Create Table If Not Exists graph_context(
	molecule_id Text,
	prefix Text,
       	suffix Text,
	CONSTRAINT namespace_pkey PRIMARY KEY (molecule_id, prefix)
	FOREIGN KEY (molecule_id) REFERENCES molecule (molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
);

Create Table If Not Exists graph_triple(
	subject Text,
	predicate Text,
	object Text
);
