Create Table If Not Exists graph_context(
	prefix Text,
	suffix Text,
	CONSTRAINT namespace_pkey PRIMARY KEY (prefix)
);

Create Table If Not Exists graph_triple(
	subject Text,
	predicate Text,
	object Text
);

Alter Table property Add Column ns text REFERENCES graph_context (prefix);
Alter Table atom_property Add Column ns text REFERENCES graph_context (prefix);
Alter Table bond_property Add Column ns text REFERENCES graph_context (prefix);

Create Table node (id Integer Primary Key, val Text, term Text, datatype Text, Unique(val,term,datatype));
Create Table nodegraph (subject_node Integer, predicate_node Integer, object_node Integer);
