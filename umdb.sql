CREATE TABLE molecule (
                molecule_id INTEGER PRIMARY KEY,
                created TIMESTAMP,
                title VARCHAR NOT NULL
);


CREATE TABLE property (
                molecule_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                value VARCHAR NOT NULL,
		FOREIGN KEY (molecule_id) REFERENCES molecule (molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE atom (
                molecule_id INTEGER NOT NULL,
                atom_number INTEGER NOT NULL,
                symbol VARCHAR,
                z INTEGER, -- atomic number
                a INTEGER, -- isostope number
                spin INTEGER,
                charge INTEGER, -- formal charge
                CONSTRAINT atom_pkey PRIMARY KEY (molecule_id, atom_number)
		FOREIGN KEY (molecule_id) REFERENCES molecule (molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE bond (
                molecule_id INTEGER NOT NULL,
                from_atom INTEGER NOT NULL,
                to_atom INTEGER NOT NULL,
                bond_order FLOAT,
                bond_type VARCHAR,
                CONSTRAINT bond_pkey PRIMARY KEY (molecule_id, from_atom, to_atom)
		FOREIGN KEY (molecule_id, from_atom) REFERENCES atom (molecule_id, atom_number) ON DELETE CASCADE ON UPDATE CASCADE
		FOREIGN KEY (molecule_id, to_atom) REFERENCES atom (molecule_id, atom_number) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE atom_property (
                molecule_id INTEGER NOT NULL,
                atom_number INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                value VARCHAR NOT NULL,
                CONSTRAINT atom_property_pkey PRIMARY KEY (molecule_id, atom_number)
		FOREIGN KEY (molecule_id, atom_number) REFERENCES atom (molecule_id, atom_number) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE bond_property (
                molecule_id INTEGER NOT NULL,
                from_atom INTEGER NOT NULL,
                to_atom INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                value VARCHAR NOT NULL,
                CONSTRAINT bond_property_pkey PRIMARY KEY (molecule_id, from_atom, to_atom)
		FOREIGN KEY (molecule_id, from_atom, to_atom) REFERENCES bond (molecule_id, from_atom, to_atom) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE coord (
                molecule_id INTEGER NOT NULL,
                atom_number INTEGER NOT NULL,
                set_number INTEGER,
                x DOUBLE,
                y DOUBLE,
                z DOUBLE,
                CONSTRAINT coord_pkey PRIMARY KEY (molecule_id, atom_number)
		FOREIGN KEY (atom_number, molecule_id) REFERENCES atom (atom_number, molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE internal_coord (
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

CREATE TABLE residue (
                molecule_id INTEGER NOT NULL,
		chain VARCHAR,
		number INTEGER,
		name VARCHAR,
                CONSTRAINT residue_pkey PRIMARY KEY (molecule_id, chain, number)
		FOREIGN KEY (molecule_id) REFERENCES molecule (molecule_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE residue_atom (
                molecule_id INTEGER NOT NULL,
		atom_number INTEGER NOT NULL,
		residue_chain VARCHAR,
		residue_number INTEGER,
		name VARCHAR,
                CONSTRAINT residue_atom_pkey PRIMARY KEY (molecule_id, atom_number)
		FOREIGN KEY (molecule_id, atom_number) REFERENCES atom (molecule_id, atom_number) ON DELETE CASCADE ON UPDATE CASCADE
		FOREIGN KEY (molecule_id, residue_chain, residue_number) REFERENCES residue (molecule_id, chain, number) ON DELETE CASCADE ON UPDATE CASCADE
);
