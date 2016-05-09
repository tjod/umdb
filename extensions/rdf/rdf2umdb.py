import sys
from umdb import umdb 
from rdflib import Graph, RDF, URIRef, Namespace 
from urlparse import urlparse, urlunparse

def counts():
  uniq_types = dict()
  types_in_graph = g.objects(subject = None, predicate = RDF.type)
  for t in types_in_graph:
    if t in uniq_types:
  	  uniq_types[t] += 1
    else:
  	  uniq_types[t] = 1
  print "Types:"
  for (t,count) in uniq_types.iteritems():
  	print t,count
  
  print "Properties:"
  uniq_props = dict()
  props = g.predicates(subject = None, object = None)
  for p in props:
    if p in uniq_props:
  	  uniq_props[p] += 1
    else:
  	  uniq_props[p] = 1
  for (p,count) in uniq_props.iteritems():
  	print p,count
  
def main():

  if len(sys.argv) > 1:
    udb = sys.argv[1]
  else:
    udb = None

  g  =  Graph()
  g.parse(sys.stdin, format = 'turtle')
  #print g.serialize(format="xml")

  # define these two to ensure no errors in code here
  gc = Namespace("http://purl.org/gc/")
  dc = Namespace("http://purl.org/dc/terms/")
  pub = g.value(predicate=RDF.type, object=gc.ComputationalChemistryPublication)
  if pub is None:
	  print "No gc.ComputationalChemistryPublication found"
	  exit()
  pubParts = urlparse(pub)
  #TODO better way to get base
  base = urlunparse( (pubParts.scheme, pubParts.netloc, '/', '', '', '') )
  id = g.value(pub, dc.identifier)

  # create database
  if udb is None: udb = id
  u = umdb(udb)
  u.create()

  #TODO insert triples

  system=g.value(predicate=RDF.type, object=gc.MolecularSystem)
  charge = g.value(g.value(system, gc.hasSystemCharge), gc.hasNumber).value
  multiplicity = g.value(g.value(system, gc.hasSystemMultiplicity), gc.hasNumber).value

  # maps bond order strings to integers, using values appropriate for openBabel; oddball is Aromatic=5
  # when bonds are stored as value strings
  bondOrderValues = ["Single", "Double", "Triple", "Dummy", "Aromatic"]
  # when bonds are stored as uri refs
  bondOrderTypes  = [gc.Single, gc.Double, gc.Triple, "Dummy", gc.Aromatic]

  # TODO: how to deal with individual molecules' charge, multiplicity
  # loop over all mols in this system
  for mol in g.subjects(RDF.type, gc.Molecule):
    u.insert_molecule(mol, multiplicity=multiplicity, charge=charge)
    u.insert_graph_context("base", base)

  # trick way to create namespaces from graph for use within this script
    for (prefix,suffix) in g.namespaces():
      globals()[prefix] = Namespace(suffix) #  may replace gc and dc from above
      # put the namespace into the database, too; for each molecule_id because for FK but also because
      # the umdb file can contain molecules from multiple sources
      u.insert_graph_context(prefix, suffix)

    # molecule properties
    u.insert_molproperty(ns="gc", name="hasInChIKey", value=g.value(mol, gc.hasInChIKey).value)

    # atoms
    idx = 0
    atoms = []
    for atom in g.objects(mol, gc.hasAtom):
      symbol = g.value(atom, gc.hasElementSymbol)
      charge = g.value(g.value(atom, gc.hasFormalCharge), gc.hasNumber)
      idx += 1
      atoms.append(atom)
      u.insert_atom(idx, name=atom, symbol=symbol, charge=charge)
      for c in g.objects(atom, gc.hasCoordinates):
  	    x = g.value(g.value(c, gc.hasAtomCoordinateX), gc.hasNumber)
  	    y = g.value(g.value(c, gc.hasAtomCoordinateY), gc.hasNumber)
  	    z = g.value(g.value(c, gc.hasAtomCoordinateZ), gc.hasNumber)
	    u.insert_atom_coord(idx, x, y, z)
      for p in g.objects(atom, gc.MullikenCharges):
  	      charge = g.value(g.value(system, gc.MullikenCharges), gc.hasNumber).value
	      u.insert_atomproperty(idx, ns="gc", name="MullikenCharges", value=charge)

    # bonds
    for bond in g.subjects(RDF.type, gc.NormalBond):
	bond_order_val = g.value(bond, gc.hasBondOrder)
	bond_type = g.value(bond, gc.hasBondType)
	if bond_order_val is None:
		bond_order = 1+bondOrderValues.index(bond_type.value)
	else:
		bond_order = 1+bondOrderTypes.index(bond_type)
	# set ensures unique entries; should only be two members/atoms
	pair = set()
	# two ways to get the atoms of this bond
	# this bond hasAtom; Jacob says this is the current way as of 5/9/2016
	for a in g.objects(bond, gc.hasAtom):
                pair.add(1+atoms.index(a))
	# or which atoms has(this)Bond; an old way I encountered
	for a in g.subjects(predicate=gc.hasBond, object=bond):
                pair.add(1+atoms.index(a))
	from_atom = pair.pop()
	to_atom = pair.pop()
        u.insert_bond(from_atom, to_atom, bond_order, name=bond)
	u.insert_bondproperty(from_atom, to_atom, ns="gc", name="hasBondType", value=bond_type)
	u.insert_bondproperty(from_atom, to_atom, ns="rdfs", name="label", value=g.label(bond).value)
	
  # get atom z(atomic number) values from symbol
  u.symbol_to_z()
  u.close()
  
if __name__ == "__main__":
  main()
