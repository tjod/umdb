Create Temporary View atom_block As Select atom.molecule_id, count(atom.number) natoms,
 group_concat(printf("%10.4f%10.4f%10.4f %-2s%3d%3.0f%3d%3d%3d",x,y,z,symbol,0,formal_charge,0,0,0,0),char(10)) records
 From atom Left Join coord On (atom.molecule_id=coord.molecule_id And atom.number=coord.atom_number) Group By atom.molecule_id Order By atom.number Asc ;

Create Temporary View bond_block As Select molecule_id, count(from_atom) nbonds, group_concat(printf("%3d%3d%3d",from_atom,to_atom,bond_order),char(10)) records
 From bond Group By molecule_id Order By from_atom Asc ;

Create Temporary View atom_list_block As Select molecule_id, group_concat(printf("M  CHG%3d %3d %3d",1,number,formal_charge), char(10)) records From atom
 Where formal_charge!=0 Group By molecule_id;

-- each section as a column
Create Temporary View molblock As
Select molecule_id, title, printf("  %-8s%10.10s", 'UMDBv1',created) line2, "" line3,
 printf("%3d%3d%3d%3d%3d%3d%12s%3d %5s", natoms, nbonds, 0, 0, 1, 0, ' ', 999, 'V2000') counts,
 atom_block.records atom_block,
 bond_block.records bond_block,
 atom_list_block.records atom_list_block
 From molecule
 Left Join atom_block Using (molecule_id)
 Left Join bond_block Using (molecule_id)
 Left Join atom_list_block Using (molecule_id)
;

-- all sections concatenated with new lines
-- coalesce to ensure null values are handled OK
Create Temporary View sdf As
Select molecule_id, coalesce(title,'')||char(10)||
 coalesce(line2,'')||char(10)||
 coalesce(line3,'')||char(10)||
 coalesce(counts,'')||char(10)||
 coalesce(atom_block||char(10),'')||
 coalesce(bond_block||char(10),'')||
 coalesce(atom_list_block||char(10),'')||
 'M  END'||char(10)||
 '$$$$' molblock from molblock;

-- Possible useage
-- Select molblock from sdf Order By molecule_id Asc;
-- Select molblock from sdf where molecule_id < 3 Order By molecule_id Asc;
-- Select molblock from sdf where molecule_id in (Select molecule_id from molecule where title like '%chloride%') Order By molecule_id Asc;
