import sys
from umdb import umdb
from rdflib import Graph, RDF, URIRef, Namespace, term
from urlparse import urlparse, urlunparse
import urllib2
import sqlite3

def counts(g):
    print "Types:"
    uniq_types = dict()
    types_in_graph = g.objects(subject = None, predicate = RDF.type)
    for t in types_in_graph:
        if t in uniq_types:
            uniq_types[t] += 1
        else:
            uniq_types[t] = 1
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

def get_graph(input):

    g  =  Graph()
    if input:
        try:
            g.parse(input)
        except urllib2.HTTPError as e:
            print "HTTP Error({0}): {1}".format(e.code, e.reason)
        except urllib2.URLError as e:
            print "URL Error: {0}".format(e.reason)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise
    else:
        g.parse(sys.stdin, format = 'turtle')

    return g

def make_umdb(g, odb):
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
    if odb is None:
        udb = id
    else:
        udb = odb
    u = umdb(udb)
    u.create()

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
        inchi = g.value(mol, gc.hasInChIKey)
        if inchi: u.insert_molproperty(ns="gc", name="hasInChIKey", value=inchi.value)

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
            to_atom = pair.pop()
            from_atom = pair.pop()
            u.insert_bond(from_atom, to_atom, bond_order, name=bond)
            u.insert_bondproperty(from_atom, to_atom, ns="gc", name="hasBondType", value=bond_type)
            u.insert_bondproperty(from_atom, to_atom, ns="rdfs", name="label", value=g.label(bond).value)

    # get atom z(atomic number) values from symbol
    u.symbol_to_z()
    u.close()

    return udb

class SQLgraph:
    def __init__(self, db):
        self.connection = sqlite3.connect(db)
        self.cursor = self.connection.cursor()
        self.cursor.execute("Create Table node (id Integer Primary Key, val Text, term Text, datatype Text, Unique(val,term,datatype))")
        self.cursor.execute("Create Table nodegraph (subject_node Integer, predicate_node Integer, object_node Integer)")

    def close(self):
        self.connection.commit()
        self.connection.close()

    def insert(self, x):
        if type(x) == term.BNode:
            return self.node(x,'bnode','')
        elif type(x) == term.URIRef:
            return self.node(x,'uri','')
        elif type(x) == term.Literal:
            return self.node(x,'literal',x.datatype)
            #return self.node(x,'literal','')

    def node(self, x, term, datatype):
        if datatype:
            self.cursor.execute("Insert Or Ignore Into node (val, term, datatype) Values (?,?,?)", [x,term,datatype])
            self.cursor.execute("Select id from node Where val = ? And term = ? And datatype = ?", [x,term,datatype])
        else:
            self.cursor.execute("Insert Or Ignore Into node (val, term) Values (?,?)", [x,term])
            self.cursor.execute("Select id from node Where val = ? And term = ? And datatype is null", [x,term])
        return self.cursor.fetchone()[0]

    def insert_triple(self, s,p,o):
        sql = "Insert Into nodegraph (subject_node, predicate_node, object_node) Values (?,?,?)"
        sid = self.insert(s)
        pid = self.insert(p)
        oid = self.insert(o)
        self.cursor.execute(sql, [sid,pid,oid])

def main():

    odb = None
    input = None
    print_counts = False
    include_graph = False
    args = sys.argv
    args.pop(0) # program name
    while len(args) > 0:
        arg = args.pop(0)
        if arg == "-h":
            print "usage: rdf2umdb [-h][-c][-g][-o output][input]"
            print "       if no input, expect stdin."
            print "       if no output given, output file name is guessed from input graph's metadata."
            print "  [-h] this message"
            print "  [-o] output umdb file name."
            print "  [-c] print counts of graph's Types(objects with predicate==rdf.Type) and Properties(predicates)."
            print "  [-g] include graph's triples in output database."
            exit()
        elif arg == "-c":
            print_counts = True
        elif arg == "-g":
            include_graph = True
        elif arg == "-o":
            arg = args.pop(0)
            odb = arg
        else:
            if input is None:
                input = arg
            else:
                print "unexpected extra arg",arg
                exit()

    #print input, odb
    g = get_graph(input)
#  print g.serialize(format="turtle")
    if print_counts: counts(g)
    udb = make_umdb(g, odb)
    if include_graph:
        print udb
        sg = SQLgraph(udb)
        for (s,p,o) in g:
            sg.insert_triple(s,p,o)
        sg.close()

if __name__ == "__main__":
    main()
