pushd "`dirname $0`" > /dev/null
cd tests
PYTHONPATH="`pwd`/../python/modules" coverage run --source ../python/modules,../sbin --branch FuntooSuite.py
coverage report -m
coverage html
exitcode=$?
popd > /dev/null
exit $exitcode
