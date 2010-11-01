pushd "`dirname $0`" > /dev/null
cd tests
if [ "$1" == "coverage" ]; then
	PYTHONPATH="`pwd`/../python/modules" coverage run --source ../python/modules,../sbin --branch FuntooSuite.py;
	coverage report -m;
	coverage html;
else
	PYTHONPATH="`pwd`/../python/modules" python FuntooSuite.py;
fi
exitcode=$?
popd > /dev/null
exit $exitcode
