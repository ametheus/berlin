#!/bin/bash

cd $(dirname $0)/../bin

for F in  berlin/config_ui.py  berlin/network_config.py \
          berlin/ruleset.py    berlin/berlin.py
do
    echo -n "Running doctests from file [$F]... "
    python $F $@
    
    if [ $? -ne 0 ]
    then
        echo ""
        echo ""
        echo ""
        echo "Some doctests failed to run."
        echo "In particular, the ones from [$F] failed miserably."
        exit 1
    fi
    
    echo "done."
done

echo ""
echo "All doctests passed with flying colours."

