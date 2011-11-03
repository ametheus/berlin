#!/bin/bash

cd $(dirname $0)/../bin

E=0

for F in  berlin/config_ui.py  berlin/network_config.py \
          berlin/ruleset.py    berlin/berlin.py         \
          berlin/qos.py
do
    echo -n "Running doctests from file [$F]... "
    python $F $@
    err=$?
    
    E=$(( E + $err ))
    if [ "$err" = 0 ]
    then
        echo "done."
    else
        echo "Doctests for file [$F] failed. (see above)"
        echo "Counting $E errors so far."
    fi
done


if [ $E -ne 0 ]
then
    echo ""
    echo ""
    echo ""
    echo "A total number of $E doctests failed to run."
    exit $E
else

    echo ""
    echo "All doctests passed with flying colours."

fi
