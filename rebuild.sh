cp $1 $1.copy
sqlite3 $1 <<EOSQL
Drop Table molecule;
Drop Table atom;
Drop Table bond;
Drop Table property;
Drop Table atom_property;
Drop Table bond_property;
Drop Table coord;
Drop Table internal_coord;
Drop Table residue;
Drop Table residue_atom;
.read umdb.sql
EOSQL
