Create Table element (
	z Integer,
	symbol Text,
	ar_electronegativity Float,
	covalent_radius Float,
	bondorder_radius Float,
	vdw_radius Float,
	max_bond_valence Float,
	mass Float,
	electronegativity Float,
	ionization Float,
	electron_Affinity Float,
	red Float,
	green Float,
	blue Float,
	name Text,
	Constraint 'atomic_number' Primary Key (z)
);
.mode tabs
.import 'element.tab' element
