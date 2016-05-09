import sys
from rdflib import Graph, RDF 

def counts(g):
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
  props_in_graph = g.predicates(subject = None, object = None)
  for p in props_in_graph:
    if p in uniq_props:
  	  uniq_props[p] += 1
    else:
  	  uniq_props[p] = 1
  for (p,count) in uniq_props.iteritems():
  	print p,count
  
def main():
  g  =  Graph()
  g.parse(sys.stdin, format = 'turtle')
  counts(g)

if __name__ == "__main__":
	main()
