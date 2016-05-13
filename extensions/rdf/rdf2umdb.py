import sys
from umdb import umdb
from rdflib import Graph, RDF, Namespace, term, util
from urlparse import urlparse, urlunparse
import urllib2

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

def get_graph(source, fmt):
    g  =  Graph()
    if source:
        if fmt is None:
            fmt = util.guess_format(source)
        try:
            g.parse(source, format=fmt)
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

def parseURI(g, uri):
    suffix = None
    prefix = None
    for (ns,base) in g.namespaces():
        if uri.startswith(base):
            prefix = ns
            suffix = uri.replace(base,'')
            break
    return (prefix, suffix)

def shorten(g, x):
    """try to turn URIRef into namsepace: style"""
    if type(x) == term.URIRef:
        (prefix,suffix) = parseURI(g, x)
        #if prefix is not None and prefix != 'base': x = prefix+':'+suffix
        if prefix is not None: x = prefix+':'+suffix
    else:
        if x.startswith('http:'): print x, type(x)
    return x

class UMDB:
    def __init__(self, graph):
        self.g = graph
        self.dbname = None
        self.mol = None
        self.u = None
        self.gc = Namespace("http://purl.org/gc/")
        self.dc = Namespace("http://purl.org/dc/terms/")
        # maps bond order strings to integers, using values appropriate for openBabel; oddball is Aromatic=5
        #  when bonds are stored as value strings
        self.bondOrderValues = ["Single", "Double", "Triple", "Dummy", "Aromatic"]
        # when bonds are stored as uri refs
        self.bondOrderTypes  = [self.gc.Single, self.gc.Double, self.gc.Triple, "Dummy", self.gc.Aromatic]
        
    def make(self, g, odb):
        # define these two to ensure no errors in code here
        gc = self.gc
        dc = self.dc
                
        pub = g.value(predicate=RDF.type, object=gc.ComputationalChemistryPublication)
        if pub is None:
            print "No gc:ComputationalChemistryPublication found"
            exit()
        pubParts = urlparse(pub)
        #TODO better way to get base
        base = urlunparse( (pubParts.scheme, pubParts.netloc, '/', '', '', '') )
        g.bind('base', base)
        ident = g.value(pub, dc.identifier)
            
        # create database
        if odb is None:
            self.dbname = ident
        else:
            self.dbname = odb
        self.u = umdb(self.dbname)
        self.u.create()
    
        # trick way to create namespaces from graph for use within this script
        for (prefix,suffix) in g.namespaces():
            #globals()[prefix] = Namespace(suffix) #  may replace gc and dc from above
            # put the namespace into the database, too; for each molecule_id because for FK but also because
            # the umdb file can contain molecules from multiple sources
            self.u.insert_graph_context(prefix, suffix)
            
        system=g.value(predicate=RDF.type, object=gc.MolecularSystem)
        charge = g.value(g.value(system, gc.hasSystemCharge), gc.hasNumber).value
        multiplicity = g.value(g.value(system, gc.hasSystemMultiplicity), gc.hasNumber).value
    
        # TODO: how to deal with individual molecules' charge, multiplicity
        # loop over all mols in this system
        for self.mol in g.subjects(RDF.type, gc.Molecule):
            self.u.insert_molecule(self.mol, multiplicity=multiplicity, charge=charge)
            #self.u.insert_graph_context("base", base)
    
            # molecule properties
            inchi = g.value(self.mol, gc.hasInChIKey)
            if inchi: self.u.insert_molproperty(ns="gc", name="hasInChIKey", value=inchi.value)
    
        atoms = self.insert_atoms()
        self.insert_bonds(atoms)
    
        # get atom z(atomic number) values from symbol
        self.u.symbol_to_z()
        self.u.commit()
    
        return self.u
    
    def insert_atoms(self):
        g = self.g
        mol = self.mol
        gc = self.gc

        idx = 0
        atoms = []
        for atom in g.objects(mol, gc.hasAtom):
            symbol = g.value(atom, gc.hasElementSymbol)
            charge = g.value(g.value(atom, gc.hasFormalCharge), gc.hasNumber)
            idx += 1
            atoms.append(atom)
            self.u.insert_atom(idx, name=atom, symbol=symbol, charge=charge)
            for c in g.objects(atom, gc.hasCoordinates):
                x = g.value(g.value(c, gc.hasAtomCoordinateX), gc.hasNumber)
                y = g.value(g.value(c, gc.hasAtomCoordinateY), gc.hasNumber)
                z = g.value(g.value(c, gc.hasAtomCoordinateZ), gc.hasNumber)
                self.u.insert_atom_coord(idx, x, y, z)                
      
        for prop in g.objects(subject=None, predicate=gc.hasAtomProperty):
            #print prop
            for pval in g.objects(prop, gc.hasPropertyValue):
                val = g.value(pval, gc.hasNumber).value
                #ref = g.value(pval, gc.hasScope)
                #TODO get atom index from ref
                ptype = g.value(pval, RDF.type)
                (suffix,prefix) = parseURI(g, ptype)
                #print  suffix+'.'+prefix, ref, charge
                self.u.insert_atomproperty(idx, ns=suffix, name=prefix, value=val)
    
        return atoms
    
    def insert_bonds(self, atoms):
        g = self.g
        gc = self.gc

        for bond in g.subjects(RDF.type, gc.NormalBond):
            bond_order_val = g.value(bond, gc.hasBondOrder)
            bond_type = g.value(bond, gc.hasBondType)
            if bond_order_val is None:
                bond_order = 1+self.bondOrderValues.index(bond_type.value)
            else:
                bond_order = 1+self.bondOrderTypes.index(bond_type)
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
            self.u.insert_bond(from_atom, to_atom, bond_order, name=bond)
            self.u.insert_bondproperty(from_atom, to_atom, ns="gc", name="hasBondType", value=bond_type)
            self.u.insert_bondproperty(from_atom, to_atom, ns="rdfs", name="label", value=g.label(bond).value)

class SQLgraph:
    def __init__(self, g, cursor):
        self.g = g
        self.cursor = cursor
        self.cursor.execute("Create Table node (id Integer Primary Key, val Text, term Text, datatype Text, Unique(val,term,datatype))")
        self.cursor.execute("Create Table nodegraph (subject_node Integer, predicate_node Integer, object_node Integer)")

    def insert(self, x):
        if type(x) == term.BNode:
            return self.node(x,'bnode','')
        elif type(x) == term.URIRef:
            return self.node(shorten(self.g,x),'uri','')
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
    source = None
    print_counts = False
    include_graph = False
    fmt = None
    args = sys.argv
    args.pop(0) # program name
    while len(args) > 0:
        arg = args.pop(0)
        if arg == "-h":
            print "usage: rdf2umdb [-h][-c][-g][-o output][input]"
            print "       if no input, expect stdin."
            print "       if no output given, output file name is guessed from input graph's metadata."
            print "  [-h] this message"
            print "  [-f] input format"
            print "  [-o] output umdb file name."
            print "  [-c] print counts of graph's Types(objects with predicate==rdf.Type) and Properties(predicates)."
            print "  [-g] include graph's triples in output database."
            exit()
        elif arg == "-c":
            print_counts = True
        elif arg == "-g":
            include_graph = True
        elif arg == "-f":
            fmt = args.pop(0)
        elif arg == "-o":
            odb = args.pop(0)
        else:
            if source is None:
                source = arg
            else:
                print "unexpected extra arg",arg
                exit()

    #print source, odb
    g = get_graph(source, fmt)
#  print g.serialize(format="turtle")
    if print_counts: counts(g)
    u = UMDB(g)
    udb = u.make(g, odb)
    if include_graph:
        sg = SQLgraph(g, udb.cursor)
        for (s,p,o) in g:
            sg.insert_triple(s,p,o)
            udb.insert_graph_triple(shorten(g,s), shorten(g,p), shorten(g,o))
    
    udb.close()
if __name__ == "__main__":
    main()
