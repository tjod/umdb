Create Table If Not Exists graph_triple(
	subject Text,
	predicate Text,
	object Text
);

Create Table node (id Integer Primary Key, val Text, term Text, datatype Text, Unique(val,term,datatype));
Create Table nodegraph (subject_node Integer, predicate_node Integer, object_node Integer);
