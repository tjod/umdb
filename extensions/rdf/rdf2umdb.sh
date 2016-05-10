#for file in $(find ttls -name '*.ttl') ; do
rm -f ttls.umdb
for file in $(ls ttls/*.ttl) ; do
  echo $file
  python rdf2umdb.py ttls.umdb < $file
done
