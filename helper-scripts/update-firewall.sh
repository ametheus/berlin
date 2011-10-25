#!/bin/sh

#
#   Copyright (C) 2011  Thijs van Dijk
#
#   This file is part of berlin.
#
#   Berlin is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Berlin is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   file "COPYING" for details.
#


cd /usr/share/berlin

GITOUT="$(git pull origin master 2>/dev/null)"

FW="rules.py|config/ad-hosts|config/malware-hosts|config/smtp-hosts|update-firewall.sh"
AP="apache"

if [ "$(echo "$GITOUT" | grep -P " ($FW)[ ]+\|")" != "" ]; then
    echo "Recreating firewall rules."
    /sbin/firewall
fi
if [ "$(echo "$GITOUT" | grep -P "$AP")" != "" ]; then
    service apache2 reload
fi

git fetch --all >/dev/null

