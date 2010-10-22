pushd "`dirname $0`" > /dev/null
cd tests
PYTHONPATH="`pwd`/../python/modules" python FuntooSuite.py
exitcode=$?
popd > /dev/null
exit $exitcode
