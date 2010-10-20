pushd "`dirname $0`"
cd tests
python FuntooSuite.py
exitcode=$?
popd
exit $exitcode
