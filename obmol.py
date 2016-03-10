import sqlite3
import sys
import os
import openbabel as ob
from umdb import umdb
import getopt

# create a umdb from any molecular structure file that openbabel can read

def getargs():

  addprop = False
  addcharges = False
  addtypes = False
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hptc")
  except getopt.GetoptError as err:
    print err
    exit()

  for opt,val in opts:
    if opt == "-h":
      print 'usage: obmol.py [-p][-h] input_file [output_database]'
      print '       -h this help'
      print '       -p include cansmiles, inchi, E/Z bond into, R/S atom info'
      print '       -t include atom types in atom properties'
      print '       -c include Gasteiger partial charges in atom properties'
      exit()
    if opt == "-p": addprop = True
    if opt == "-t": addtypes = True
    if opt == "-c": addcharges = True

  fullfile = args[0]
  if not os.path.exists(fullfile):
    print 'usage: obmol.py input_file [output_database]'
    exit()
  fhead, ftail = os.path.split(fullfile)
  filename, fileext = os.path.splitext(ftail)
  fileext = fileext.replace('.','')

  if len(args) > 1:
    out = args[1]
  else:
    out = './' + filename + '.umdb'

  if os.path.exists(out):
    print out, 'file will not be over-written'
    exit()

  return (fullfile, fileext, out, addprop, addcharges, addtypes)

def properties(umdbout, obmol):
  from nams import chirality
  from nams import doubleb_e_z
  # add some extra properties available from openbabel
  obc = ob.OBConversion()
  obc.SetOptions('-n', obc.OUTOPTIONS) # no name

  obc.SetOutFormat('can')
  cansmiles = None
  cansmiles = obc.WriteString(obmol,1)
  if cansmiles: umdbout.insert_molproperty('OpenBabel cansmiles', cansmiles)

  # waited to insert_molproperties so that canonical smiles order gets included
  umdbout.insert_molproperties(obmol)
  canorder = umdbout.cansmiles_atom_order(obmol)

  obc.SetOutFormat('inchi')
  inchi = None
  inchi = obc.WriteString(obmol,1)
  if inchi: umdbout.insert_molproperty('InChI', inchi)

  chir = chirality.Chirality(cansmiles, 'smi')
  # chir cansmiles atoms include H atoms, but canorder does not, so keep track of offset
  nhatoms = 0
  chioffset = []
  for atom_id in range(chir.n_atoms):
    chioffset.append(nhatoms)
    if chir.obmol.GetAtom(atom_id+1).GetAtomicNum()==1 : nhatoms += 1
    atom_chir = chir.get_chirality(atom_id)
    #1 -> R; -1 -> S; 0 -> none.
    if atom_chir:
      #umdbout.insert_atomproperty(canorder[atom_id-nhatoms], 'chirality', 'R' if chir.get_chirality(atom_id) == 1 else 'S')
      umdbout.insert_atomproperty(canorder[atom_id-chioffset[atom_id]], 'NAMS chirality', 'R' if chir.get_chirality(atom_id) == 1 else 'S')

  stereo=doubleb_e_z.Stereodoubleb(cansmiles, 'smi')
  for bond_id in range(stereo.n_bonds):
    #1 -> Z; -1 -> E; 0 -> none. 
    bond_stereo = stereo.get_e_z_bond(bond_id)
    #bond = chir.obmol.GetBond(bond_id)
    #fromatom = bond.GetBeginAtomIdx()
    #toatom = bond.GetEndAtomIdx()
    #if bond_stereo: print bond_id, fromatom, toatom, bond.GetBondOrder(), bond_stereo
    if bond_stereo:
      bond = chir.obmol.GetBond(bond_id)
      fromatom = bond.GetBeginAtomIdx()-1
      toatom = bond.GetEndAtomIdx()-1
      #print bond_id, fromatom, toatom, canorder[fromatom-chioffset[fromatom]], canorder[toatom-chioffset[toatom]], bond.GetBondOrder()
      umdbout.insert_bondproperty(canorder[fromatom-chioffset[fromatom]], canorder[toatom-chioffset[toatom]], 'NAMS EZ-stereo', 'Z' if bond_stereo == 1 else 'E')
# end of properties()

def main():

  (fullfile, fileext, out, addprop, addcharges, addtypes) = getargs()
  obconversion = ob.OBConversion()
  if obconversion.SetInFormat(fileext):
    pass
  else:
    print "can't process file type"
    exit()

  print addprop, addcharges, addtypes

  obmol = ob.OBMol()
  notatend = obconversion.ReadFile(obmol, fullfile)
  umdbout = umdb(out)
  umdbout.create()
  n = 0
  while notatend:
    n += 1
    sys.stderr.write(str(n)+'\r')
    umdbout.insert_mol(obmol)
    umdbout.insert_molproperty('File source', fullfile)
    if obmol.NumAtoms() > 0:
      if addcharges: umdbout.insert_atomcharges(obmol)
      if addtypes: umdbout.insert_atomtypes(obmol)
    if addprop:
      properties(umdbout, obmol)
    else:
      umdbout.insert_molproperties(obmol)
    obmol = ob.OBMol()
    notatend = obconversion.Read(obmol)
  umdbout.close()

if __name__ == "__main__":
  main()
