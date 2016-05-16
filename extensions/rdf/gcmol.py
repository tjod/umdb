from rdflib import RDF, Namespace, term
from urlparse import urlparse, urlunparse
from umdb import umdb as umdbCore

class umdb:    
    """methods to read bits of a graph to populate umdb molecule, atom, bond, etc. tables"""
    def __init__(self):
        self.g = None
        self.dbname = None
        self.mol = None
        self.udb = None
        self.cursor = None
        # graph's atoms URIRefs function as names, stored here to enable bond table to use idx
        self.atoms = []
        # define these two to ensure no errors in code here
        self.gc = Namespace("http://purl.org/gc/")
        self.dc = Namespace("http://purl.org/dc/terms/")
        # maps bond order strings to integers, using values appropriate for openBabel; oddball is Aromatic=5
        #  when bonds are stored as value strings
        self.bondOrderValues = ["Single", "Double", "Triple", "Dummy", "Aromatic"]
        # when bonds are stored as uri refs
        self.bondOrderTypes  = [self.gc.Single, self.gc.Double, self.gc.Triple, "Dummy", self.gc.Aromatic]
        
    def parseURI(self, uri):
        """parse a URIRef into a prefix(in graph namespaces) and suffix"""
        suffix = None
        prefix = None
        for (ns,base) in self.g.namespaces():
            if uri.startswith(base):
                prefix = ns
                suffix = uri.replace(base,'')
                break
        return (prefix, suffix)
    
    def shortenURI(self, x):
        """try to turn URIRef into namsepace prefix:suffix style"""
        if type(x) == term.URIRef:
            (prefix,suffix) = self.parseURI(self.g, x)
            # do we allow to shorten base?
            #if prefix is not None and prefix != 'base': x = prefix+':'+suffix
            if prefix is not None: x = prefix+':'+suffix
        return x
    
    def create(self, g, odb):
        """create the database, guessing a name if necessary"""
        self.g = g
        
        pub = g.value(predicate=RDF.type, object=self.gc.ComputationalChemistryPublication)
        if pub is None:
            print "No gc:ComputationalChemistryPublication found"
            exit()
        pubParts = urlparse(pub)
        #TODO better way to get base
        base = urlunparse( (pubParts.scheme, pubParts.netloc, '/', '', '', '') )
        g.bind('base', base)
        ident = g.value(pub, self.dc.identifier)
            
        # create database
        if odb is None:
            self.dbname = ident
        else:
            self.dbname = odb
        self.udb = umdbCore(self.dbname)
        self.udb.create()
        # borrow the SQLite cursor from the umdb database
        self.cursor = self.udb.cursor
        
    def make(self):
        """public method to find all the bits of the graph and make the umdb"""
        
        #handy
        g = self.g
                        
        # add tables for rdf triples, context, etc.
        self.cursor.execute("Select count(*) from sqlite_master Where tbl_name='graph_context'")
        if self.cursor.fetchone()[0] == 0:
            script = open('rdf.sql').read()
            self.cursor.executescript(script)
    
        for (prefix,suffix) in g.namespaces():
            # trick way to create namespaces from graph for use within this script
            #globals()[prefix] = Namespace(suffix) #  may replace gc and dc from above
            # put the namespace into the database, too; for each molecule_id because for FK but also because
            self.insert_graph_context(prefix, suffix)

        self.insert_mol()
        self.insert_atoms()
        self.insert_bonds()
    
        # get atom z(atomic number) values from symbol
        self.udb.symbol_to_z()
        self.udb.commit()
        
    def insert_mol(self):
        """find the system and mol, insert into tables"""
        # TODO: how to deal with individual molecules' charge, multiplicity
        
        #handy
        gc = self.gc
        g = self.g
                       
        system=g.value(predicate=RDF.type, object=gc.MolecularSystem)
        charge = g.value(g.value(system, gc.hasSystemCharge), gc.hasNumber).value
        multiplicity = g.value(g.value(system, gc.hasSystemMultiplicity), gc.hasNumber).value
        
        # loop over all mols in this system
        for self.mol in g.subjects(RDF.type, gc.Molecule):
            self.udb.insert_molecule(self.mol, multiplicity=multiplicity, charge=charge)
            #self.udb.insert_graph_context("base", base)
    
            # molecule properties
            inchi = g.value(self.mol, gc.hasInChIKey)
            if inchi: self.udb.insert_molproperty(ns="gc", name="hasInChIKey", value=inchi.value)
    
    def insert_atoms(self):
        """find the mol atoms and insert into tables"""
        g = self.g
        mol = self.mol
        gc = self.gc

        # idx will be the atom_number in the umdb
        idx = 0

        for atom in g.objects(mol, gc.hasAtom):
            symbol = g.value(atom, gc.hasElementSymbol)
            charge = g.value(g.value(atom, gc.hasFormalCharge), gc.hasNumber)
            idx += 1
            self.atoms.append(atom)
            self.udb.insert_atom(idx, name=atom, symbol=symbol, charge=charge)
            for c in g.objects(atom, gc.hasCoordinates):
                x = g.value(g.value(c, gc.hasAtomCoordinateX), gc.hasNumber)
                y = g.value(g.value(c, gc.hasAtomCoordinateY), gc.hasNumber)
                z = g.value(g.value(c, gc.hasAtomCoordinateZ), gc.hasNumber)
                self.udb.insert_atom_coord(idx, x, y, z)                

        #TODO atom gc.hasScope os broken in all turtle examples, so far      
        for prop in g.objects(subject=None, predicate=gc.hasAtomProperty):
            #print prop
            for pval in g.objects(prop, gc.hasPropertyValue):
                val = g.value(pval, gc.hasNumber).value
                #ref = g.value(pval, gc.hasScope)
                #TODO get atom index from ref
                ptype = g.value(pval, RDF.type)
                (suffix,prefix) = self.parseURI(ptype)
                #print  suffix+'.'+prefix, ref, charge
                self.udb.insert_atomproperty(idx, ns=suffix, name=prefix, value=val)
    
    def insert_bonds(self):
        """find the bonds and insert into tables"""
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
                pair.add(1+self.atoms.index(a))
            # or which atoms has(this)Bond; an old way I encountered
            for a in g.subjects(predicate=gc.hasBond, object=bond):
                pair.add(1+self.atoms.index(a))
            to_atom = pair.pop()
            from_atom = pair.pop()
            self.udb.insert_bond(from_atom, to_atom, bond_order, name=bond)
            self.udb.insert_bondproperty(from_atom, to_atom, ns="gc", name="hasBondType", value=bond_type)
            self.udb.insert_bondproperty(from_atom, to_atom, ns="rdfs", name="label", value=g.label(bond).value)

    def insert_node(self, x):
        """store the node depending on its type"""
        if type(x) == term.BNode:
            return self.node(x,'bnode','')
        elif type(x) == term.URIRef:
            return self.node(self.shortenURI(self.g,x),'uri','')
        elif type(x) == term.Literal:
            return self.node(x,'literal',x.datatype)
            #return self.node(x,'literal','')

    def node(self, x, term, datatype):
        """insert the node along with its type and return its id"""
        if datatype:
            self.cursor.execute("Insert Or Ignore Into node (val, term, datatype) Values (?,?,?)", [x,term,datatype])
            self.cursor.execute("Select id from node Where val = ? And term = ? And datatype = ?", [x,term,datatype])
        else:
            self.cursor.execute("Insert Or Ignore Into node (val, term) Values (?,?)", [x,term])
            self.cursor.execute("Select id from node Where val = ? And term = ? And datatype is null", [x,term])
        return self.cursor.fetchone()[0]

    def insert_triple(self, s,p,o):
        """public method to insert a triple"""
        sql = "Insert Into nodegraph (subject_node, predicate_node, object_node) Values (?,?,?)"
        sid = self.insert_node(s)
        pid = self.insert_node(p)
        oid = self.insert_node(o)
        self.cursor.execute(sql, [sid,pid,oid])
        
    def insert_graph_context(self, prefix, suffix):
        """namespace and name for the context, ala tutrle, json-ld"""
        sql = "Insert Into graph_context (prefix, suffix) Values (?,?)"
        sqlargs = [prefix, suffix]
        self.cursor.execute(sql, sqlargs)

    def insert_graph_triple(self, s, p, o):
        """insert the raw graph triple"""
        sql = "Insert Into graph_triple (subject, predicate, object) Values (?,?,?)"
        sqlargs = [s,p,o]
        self.cursor.execute(sql, sqlargs)

    def close(self):
        """close the index to speed up references to the nodegraph table"""
        self.cursor.execute("Create Index node_index On nodegraph (subject_node, predicate_node, object_node)")
        self.udb.close()