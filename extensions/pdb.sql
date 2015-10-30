-- .width 6 5 4 1 3 1 4 1 8 8 8 6 6 2 2
Create Temporary View atoms As
Select atom.molecule_id, "ATOM  " rectype, atom.atom_number, ra.name name, " " alt, residue.name resname, residue.chain, residue.number resnum, " " icode,
  coord.x, coord.y, coord.z, 1.0 occ, 0.0 temp, atom.symbol From atom
 Left Join residue_atom ra Using (molecule_id, atom_number)
 Left Join residue Using (molecule_id, chain, number)
 Left Join coord Using (molecule_id, atom_number);

Create Temporary View pdb As
Select printf("%6s%5s %4s%1s%3s %1s%4d%1s   %8.3f%8.3f%8.3f%6.2f%6.2f          %2s%2s", rectype, atom_number, name, alt, resname, chain, resnum, icode, x, y, z, occ, temp, symbol)
 from atoms Order By atom_number Asc;
