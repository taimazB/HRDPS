source ./configs.sh


function total {
	field=$1
	i=$2
	lastFile=$(ls *.nc | head -$i | tail -1 | sed "s/${field}/TOTAL${field}/")
	cdo -enssum -chname,${field},TOTAL${field} $(ls *.nc | head -$i) ${MAIN}/nc/TOTAL${field}/${lastFile}
}
export -f total

for field in CONDALPCPN CONDASSN; do
	mkdir ${MAIN}/nc/TOTAL${field}
	cd ${MAIN}/nc/${field}
	parallel "total ${field} {}" ::: {1..48}
done


cd ${MAIN}
python3 scripts/cnv.py


for d in $(find nc -name tiles*); do
    mkdir ${MAIN}/${d}/frames
    cd ${MAIN}/${d}/frames
    i=1
    for f in ../*.png; do
	# for c in $(seq 1 $n); do
	I=$(printf %03d $i)
	ln -s $f ${I}.png
	i=$((i + 1))
	# done
    done
done
