#! /bin/sh

# mnsmitasin 2016-02-25
# This script just parses the top movers and outputs the MD file for including in the dashboard

# OUTFILE="react-network-diagrams/examples/markdown/trafficmap.md"
OUTFILE="mnsmitasin_md_example.md"
FACILITIES="ALS"

for FACILITY in $FACILITIES
do
  FILES=$(ls $FACILITY)
  SRC=$(cat $FACILITY/$FILES | cut -d":" -f5 | cut -d"," -f1 | sort | uniq | cut -d"}" -f1 | tr -d \" | grep -v "0\.0\.0\.0")
  DSTLIST=$(cat $FACILITY/$FILES | cut -d":" -f6 | sort | uniq | cut -d"}" -f1 | tr -d \" | grep -v "0\.0\.0\.0")
done

SRC_DNS=$(dig +short -x $SRC)

echo "### TOP MOVERS" > $OUTFILE
echo "" >> $OUTFILE

SUM="0"

for DST in $DSTLIST
do
  # Return list of flow bytes for each destination
  DSTFLOWS=$(fgrep "$DST" $FACILITY/$FILES | cut -d ":" -f4 | cut -d"," -f1 | tr -d '\"')
  # For each flow in the list, add the bytes
  for FLOW in $DSTFLOWS
  do
     SUM=$(echo "$SUM + $FLOW" | bc)
     # echo "$SRC -> $DST : $FLOW"
  done
  DST_DNS=$(dig +short -x $DST)
  if [ -z $DST_DNS ]
  then
    continue
  else
  BtoGB=$(echo "$SUM / 1024 / 1024 / 1024" | bc)
  echo "$SRC_DNS -> $DST_DNS : $BtoGB Gbytes" >> $OUTFILE
  echo "" >> $OUTFILE
  # clear SUM
  SUM="0"
fi
done

cat $OUTFILE
