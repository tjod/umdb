import sys
from gcmol import umdb
from rdflib import Graph, RDF, util
import urllib2

def counts(g):
    """Get a count of various triples in a graph"""
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
    """parse the graph, guessing the type if necessary"""
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

def main():
    """make a umdb SQLite database from an input graph"""

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
    u = umdb()
    u.create(g, odb)
    u.make()
    if include_graph:
        for (s,p,o) in g:
            u.insert_triple(s,p,o)
            u.insert_graph_triple(u.shortenURI(s), u.shortenURI(p), u.shortenURI(o))

    u.close()
if __name__ == "__main__":
    main()
