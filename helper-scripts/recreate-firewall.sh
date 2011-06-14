#!/bin/sh

#
#   Copyright (C) 2011  Thijs van Dijk
#
#   This file is part of vuurmuur.
#
#   Vuurmuur is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Vuurmuur is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   file "COPYING" for details.
#


cd /usr/share/vuurmuur/bin
python rules.py


/sbin/iptables-restore < /etc/vuurmuur/rules
mkdir -p /etc/vuurmuur/old.rules
cp /etc/vuurmuur/rules "/etc/vuurmuur/old.rules/rules-$(date '+%F %T')"
